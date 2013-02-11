import re

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from errors.models import ErrorSet, Error, ERROR_LEVEL, ERROR_SET_SOURCES

from articleflow.models import Article, ArticleState, State, Journal
from errors.models import Error, ErrorSet

import MySQLdb
from datetime import datetime

#s_host = "sfo-db01.int.plos.org"
#s_user = "article_tracker"
#s_passwd = "pqeCKYxL"
#s_db = "article_tracker"

s_host = ""
s_user = "ai_leg"
s_passwd = ""
s_db = "ai_leg"

def get_or_create_user(username):
    if not username:
        return None
    try:
        u = User.objects.get(username=username)
    except User.DoesNotExist:
        u = User(username=username, password='veryinsecurepassword')
        u.save()
    return u
        

def get_journal_from_doi(doi):
    match = re.match('.*(?=\.)', doi)
    
    if not match:
        raise ValueError('Could not find a journal short_name in doi, %s' % doi)
    short_name = re.match('.*(?=\.)', doi).group(0)
    
    try:
        return Journal.objects.get(short_name=short_name)
    except Journal.DoesNotExist:
        raise ValueError("doi prefix, %s, does not match any known journal" % short_name)

def date_from_string(s):
    print "ATTEMPTING TO CONVERT %s" % s
    try:
        return datetime.strptime(s, "%m/%d/%Y")
    except ValueError:
        try:
            return datetime.strptime(s, "%Y-%m-%d")
        except ValueError:
            try:
                return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
            except ValueError, e:
                print e
                return None
            
    except TypeError:
        return None

def datetime_from_string(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            return datetime.strptime(s, "%Y/%m/%d %H:%M:%S")
        except ValueError:
            return None
            print s
    except TypeError, e:
        print e
        return None

def separate_errors(e):
    if not e:
        return []
    errors_raw = e.strip().splitlines(False)
    
    errors=[]
    for error in errors_raw:
        error_tuple = (error, 1)
        #print "Raw: %s" % error
        for i, level in ERROR_LEVEL:
            
            p = re.compile('(?<=%s:).*' % level, re.IGNORECASE)
            m = p.search(error) 
            if m:
                #print "Match: %s" % m.group(0)
                error_tuple = (m.group(0).strip(), i)
                break

        errors += [error_tuple]
    
    return errors


class DBBase(object):
    def __init__(self):
        self.at_db = MySQLdb.connect(host= s_host,
                                     user=s_user,
                                     passwd=s_passwd,
                                     db=s_db)
        self.at_c = self.at_db.cursor(cursorclass=MySQLdb.cursors.DictCursor)

class GhettoState(object):
    def __init__(self, doi, timestamp, state_name, effecting_user=None, assigned_user=None):
        self.timestamp = timestamp
        self.state_name = state_name
        self.effecting_user = effecting_user
        self.assigned_user = assigned_user

    def __unicode__(self):
        return "timestamp: %s, state_name: %s, effecting_user: %s, assigned_user: %s" % (self.timestamp, self.state_name, self.effecting_user, self.assigned_user)

    def save(self, article=None):
        if not article:
            article = Article.objects.get(doi=self.doi)
       
        e_user = get_or_create_user(self.effecting_user)
        a_user = get_or_create_user(self.assigned_user)
        print self.state_name
        state = State.objects.get(name=self.state_name)
        a_s, new = ArticleState.objects.get_or_create(article=article,
                                                     created=self.timestamp,
                                                     assignee=a_user,
                                                     from_transition_user=e_user,
                                                     state=state) 
        if new:
            a_s.save()
        

class GhettoIssue(object):
    def __init__(self, doi, timestamp, user, feedback):
        self.timestamp = timestamp
        self.user = user
        self.feedback = feedback

    def __unicode__(self):
        return "timestamp: %s, user: %s, feedback: %s" % (self.timestamp, self.user, self.feedback)

class GhettoNote(object):
    def __init__(self, doi, timestamp, user, note):
        self.timestamp = timestamp
        self.user = user
        self.note = note

    def __unicode__(self):
        return "timestamp: %s, user: %s, note: %s" % (self.timestamp, self.user, self.note)

class MigrateDOI(DBBase):
    def __init__(self, doi):
        super(MigrateDOI, self).__init__()
        self.doi = doi
        self.pubdate = None
        self.states = []
        self.errorsets = []
        self.md5 = None
        self.si_guid = None
        self.feedback = []
        self.notes = []

    def grab_pulls(self):
        self.at_c.execute(
            """
            SELECT
              ap.pubdate as 'pubdate',
              ap.time as 'pulltime',
              ap.errors as 'errors',
              ap.user as 'user',
              ap.md5 as 'md5',
              ap.si_guid as 'si_guid'
            FROM article_pulls as ap
            WHERE ap.errors is not Null
              AND ap.errors not like ''
              AND ap.doi = '%s'
            ORDER BY ap.pull_time desc
            """ % self.doi)

        pulls = self.at_c.fetchall()
        
        for pull in pulls:
            self.states += [(pull['pulltime'], GhettoState(self.doi, pull['pulltime'], 'Pulled', effecting_user=pull['user']))]
            pull['pubdate'] = date_from_string(pull['pubdate'])
            if pull['pubdate']:
                self.pubdate = pull['pubdate']
            pull['errors'] = separate_errors(pull['errors'])
            self.md5 = pull['md5']
            self.si_guid = pull['si_guid']
            
        self.errorsets = pulls

    def grab_production_assigned(self):
        self.at_c.execute(
            """
            SELECT 
              pa.*
            FROM prod_assigned AS pa
            WHERE pa.doi = '%s'
            """ % self.doi)

        assigns = self.at_c.fetchall()

        for assign in assigns:
            self.states += [(assign['time'], GhettoState(self.doi, assign['time'], 'Ready for QC (CW)', assigned_user=assign['assigned']))]

    def grab_production_feedback(self):
        self.at_c.execute(
            """
            SELECT 
              pf.*
            FROM production_feedback AS pf
            WHERE pf.doi = '%s'
            """ % self.doi)

        feedback = self.at_c.fetchall()
        
        for f in feedback:
            self.feedback += [(f['time'], GhettoIssue(self.doi, f['time'], f['user'], f['feedback']))]

    def grab_web_assigned(self):
        self.at_c.execute(
            """
            SELECT 
              wqca.*
            FROM web_qc_assigned AS wqca
            WHERE wqca.doi = '%s'
            """ % self.doi)

        assigned = self.at_c.fetchall()

        for a in assigned:
            print a
            if a['assigned'] != 'OK':
                self.states += [(a['time'], GhettoState(self.doi, a['time'], 'Needs Web Corrections (CW)', assigned_user=a['assigned'], effecting_user=a['user']))]
            else:
                self.states += [(a['time'], GhettoState(self.doi, a['time'], 'Ready to Publish'))]
            
    def grab_web_notes(self):
        self.at_c.execute(
            """
            SELECT 
              wqcn.*
            FROM web_qc_notes AS wqcn
            WHERE wqcn.doi = '%s'
            """ % self.doi)
        
        notes = self.at_c.fetchall()
        
        for n in notes:
            self.notes += [(n['time'], GhettoNote(self.doi, n['time'], n['user'], n['notes']))]

    def grab_web_qc_pubbed_stage(self):
        self.at_c.execute(
            """
            SELECT 
              wqcps.*
            FROM web_qc_pubbed_stage AS wqcps
            WHERE wqcps.doi = '%s'
            """ % self.doi)

        pubs = self.at_c.fetchall()
        
        for p in pubs:
            self.states += [(p['time'], GhettoState(self.doi, p['time'], 'Published on Stage', effecting_user=p['user']))]

    def read_from_legacy(self):
        self.grab_pulls()
        self.grab_production_assigned()
        self.grab_production_feedback()
        self.grab_web_assigned()
        self.grab_web_notes()
        self.grab_web_qc_pubbed_stage()

        print "STATES:"
        for state in self.states:
            print "state:"
            print state[1]
        print "ERRORSETS:"
        for e in self.errorsets:
            print e

        print "FEEDBACK:"
        for f in self.feedback:
            print f[1]

        print "NOTES:"
        for n in self.notes:
            print n[1]

    def write_article(self):
        journal = get_journal_from_doi(self.doi)
        a, new = Article.objects.get_or_create(doi=self.doi, journal=journal)
        print self.pubdate
        if self.pubdate:
            a.pubdate = self.pubdate
        else:
            a.pubdate = '1900-01-01'
        a.si_guid = self.si_guid
        a.md5 = self.md5

        a.save()

        return a

    def write_to_current(self):
        print "BEGIN WRITE"
        self.feedback = self.feedback.sort(key=lambda r: r[0])
        self.notes = self.notes.sort(key=lambda r: r[0])

        a = self.write_article()
        for d, s in sorted(self.states, key=lambda i: i[0]):
            s.save(a)
        

    def migrate(self):
        self.read_from_legacy()
        self.write_to_current()
        
        

class GrabAT(DBBase):
    def get_distinct_dois(self):
        self.at_c.execute(
            """
            SELECT
              DISTINCT(ap.doi)
            FROM article_pulls AS ap
            ORDER BY ap.pull_time desc
            Limit 100;
            """)
        
        dois = [i['doi'] for i in self.at_c.fetchall()]
        return dois

    def get_pull_dois(self):
        self.at_c.execute(
            """
            SELECT
              ap.doi as 'doi',
              ap.pubdate as 'pubdate',
              ap.time as 'pulltime',
              ap.errors as 'errors'
            FROM article_pulls as ap
            WHERE ap.errors is not Null
              AND ap.errors not like ''
            ORDER BY ap.pull_time desc
            Limit 100;
            """)
        
        pulls = self.at_c.fetchall()

        for pull in pulls:
            pull['pubdate'] = date_from_string(pull['pubdate'])
            pull['errors'] = separate_errors(pull['errors'])

        return pulls
        

def main():
    g = GrabAT()
    dois = g.get_distinct_dois()
    for doi in dois:
        print "###DOI: %s" % doi
        m = MigrateDOI(doi)
        m.migrate()        
    #m = MigrateDOI('pone.0016714')
    #m = MigrateDOI('pone.0029752')
    #m.migrate()
    #g.get_pull_dois()

if __name__ == '__main__':
    main()

class Command(BaseCommand):
    def handle(self, *args, **options):
        main()
