import MySQLdb
from datetime import datetime

s_host = "sfo-db01.int.plos.org"
s_user = "article_tracker"
s_passwd = "pqeCKYxL"
s_db = "article_tracker"

def date_from_string(s):
    try:
        return datetime.strptime(s, "%m/%d/%Y")
    except ValueError:
        try:
            return datetime.strptime(s, "%Y-%m-%d")
        except ValueError:
            return None
            print s
    except TypeError:
        return None

def separate_errors(e):
    if not e:
        return []
    #if e == '\n':
    #    return []
    errors = e.strip().splitlines(False)
    #print errors
    return errors

class GrabAT():    
    def __init__(self):
        self.at_db = MySQLdb.connect(host= s_host,
                                     user=s_user,
                                     passwd=s_passwd,
                                     db=s_db)
        self.at_c = self.at_db.cursor(cursorclass=MySQLdb.cursors.DictCursor)

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
        

if __name__ == '__main__':
    g = GrabAT()
    g.get_pull_dois()
