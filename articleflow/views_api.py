from django.views.generic.base import View
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt

from articleflow.models import Article, ArticleState, State, Transition, Journal, AssignmentRatio, Typesetter
from errors.models import ErrorSet, Error, ERROR_LEVEL, ERROR_SET_SOURCES
from django.contrib.auth.models import Group, User

import sys
import simplejson
import re

import logging
logger = logging.getLogger(__name__)

def resolve_choice_index(choices, key):
    for choice in choices:
        if key == choice[1]:
            return choice[0]
    return None

def separate_errors(e):
    if not e:
        return []
    errors_raw = e.strip().splitlines(False)
    
    errors=[]
    for error in errors_raw:
        if not error:
            continue
        error_tuple = (error, 1)
        logger.debug("Raw: %s" % error)
        for i, level in ERROR_LEVEL:
            
            p = re.compile('(?<=%s:).*' % level, re.IGNORECASE)
            m = p.search(error) 
            if m:
                logger.debug("Match: %s" % m.group(0))
                error_tuple = (m.group(0).strip(), i)
                break

        errors += [error_tuple]
    
    return errors

def get_journal_from_doi(doi):
    match = re.match('.*(?=\.)', doi)
    
    if not match:
        raise ValueError('Could not find a journal short_name in doi, %s' % doi)
    short_name = re.match('.*(?=\.)', doi).group(0)
    
    try:
        return Journal.objects.get(short_name=short_name)
    except Journal.DoesNotExist:
        raise ValueError("doi prefix, %s, does not match any known journal" % short_name)

#API stuff
class BaseTransaction(View):
    def get_val(self, key, dic=None):
        if not dic:
            dic = self.payload
        try:
            return dic[key]
        except KeyError:
            return None

    # override me
    def valid_payload(self):
        return True

    # override me
    def control(self):
        return True

    def parse_payload(self, json_str):
        try:
            self.payload = simplejson.loads(json_str)
        except:
            e = sys.exc_info()[0]
            logger.error("Couldn't parse json: %s" % e)
            return (self.error_response("Unable to parse json message: %s" % e), True)

        if not self.valid_payload():
            print "not valid payload"
            return (self.error_response("Invalid data in payload"), True)
        return (None, False)
    
    def response(self, message_dict, status_code=200):
        r = HttpResponse(simplejson.dumps(message_dict), mimetype='application/json')
        r.status_code = status_code
        return r

    def error_response(self, message, status_code=400):
        payload = {
            'error': message
            }
        return self.response(payload, status_code=status_code) 

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(BaseTransaction, self).dispatch(*args, **kwargs)


class TransactionArticle(BaseTransaction):
    def valid_payload(self):
        logger.debug("API transaction article received payload: %s" % self.payload)
        self.payload['doi'] = self.doi

        try:
            self.payload['journal']=get_journal_from_doi(self.payload['doi']).pk
        except ValueError:
            logger.error("Can't resolve journal")
            return False

        try:
            match = re.match('[0-9]{4}-[0-9]{2}-[0-9]{2}$', self.payload['pubdate'])
            if not match:
                logger.error("Incorrect pubdate format")
                return False
        except KeyError:
            pass

        try:
            requested_state = self.payload['state']
            state=State.objects.get(name=requested_state)
        except State.DoesNotExist:
            logger.error("Nonexistant state")
            return False
        except KeyError:
            pass

        try:
            username = self.payload['state_change_user']
            user=User.objects.get(username=username)
        except User.DoesNotExist:
            logger.error("User Doesn't exist")
            return False
        except KeyError:
            pass

        try:
            typesetter = self.payload['typesetter']
            t=Typesetter.objects.get(name=typesetter)
        except Typesetter.DoesNotExist:
            choices = [ts.name for ts in Typesetter.objects.all()]
            logger.error("Typesetter, %s, not recognized. Available choices: %s" % (typesetter, choices))
            return False
        except KeyError:
            pass

        return True

    def control(self):
        a, new = Article.objects.get_or_create(doi=self.get_val('doi'),
                                               journal=Journal.objects.get(pk=self.get_val('journal')))

        if self.get_val('pubdate'):
            a.pubdate=self.get_val('pubdate')
        if self.get_val('md5'):
            a.md5=self.get_val('md5')
        if self.get_val('si_guid'):
            a.si_guid=self.get_val('si_guid')
        if self.get_val('typesetter'):
            a.typesetter=Typesetter.objects.get(name=self.get_val('typesetter'))

        logger.debug("API finding journal: %s" % self.payload['journal'])
        a.journal=Journal.objects.get(pk=self.get_val('journal'))
                                          
        logger.debug("API New article? %s" % new)
        a.save()

        requested_state = self.get_val('state')
        if requested_state:
            if a.current_state.name != requested_state:
                logger.debug("API setting state for article: %s, %s" % (a, requested_state))
                s = ArticleState(article=a,
                                 state=State.objects.get(name=requested_state)
                                 )
                s.save()
        if self.get_val('state_change_user'):
            logger.debug("Setting from_transition_user to %s" % self.get_val('state_change_user'))
            s = a.current_articlestate
            s.from_transition_user = User.objects.get(username=self.get_val('state_change_user'))
            s.save()
        return self.payload

    def put(self, request, *args, **kwargs):
        self.doi = kwargs['doi']
        response, fail = self.parse_payload(request.body)
        if fail:
            return response

        # make change
        response_dict = self.control()

        return self.get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        try:
            a = Article.objects.get(doi=kwargs['doi'])
        except Article.DoesNotExist:
            return self.error_response('Article does not exist')
        
        pubdate_str = None
        if a.pubdate:
            pubdate_str = a.pubdate.strftime("%Y-%m-%d")

        assignee = None
        if a.current_articlestate.assignee:
            assignee = a.current_articlestate.assignee.username

        a_dict = {'doi': a.doi,
                  'pubdate': pubdate_str,
                  'state': a.current_state.name,
                  'si_guid': a.si_guid,
                  'md5': a.md5,
                  'assignee': assignee,
                  }

        return self.response(a_dict)
                                   

class TransactionErrorset(BaseTransaction):
    def valid_payload(self):
        logger.debug("Validating Errorset transaction payload")
        try:
            self.article = Article.objects.get(doi=self.doi)
        except Article.DoesNotExist:
            logger.error("That article doesn't exist")
            return False

        try:
            self.source_i = resolve_choice_index(ERROR_SET_SOURCES, self.payload['source'])
            if not self.source_i:
                logger.error("Source doesn't exist")
                return False
        except KeyError:
            logger.error("Didn't supply source")
            return False

        try:
            self.payload['errors']
        except KeyError:
            logger.error("Didn't supply errors")
            return False

        return True
        
    def control(self):
        es = ErrorSet(source=self.source_i,
                      article=self.article)
        es.save()
        for error, level in separate_errors(self.payload['errors']):
            e = Error(message=error,
                      level=level,
                      error_set=es)
            e.save()
        

    def put(self, request, *args, **kwargs):
        self.doi = kwargs['doi']
        self.errorset_pk = kwargs['errorset_pk']
        response, fail = self.parse_payload(request.body)
        if fail:
            return response

        self.control()
        return self.response(self.payload)


    def get(self, request, *args, **kwargs):
        return self.error_response("Not Implemented")

class TransactionTransition(BaseTransaction):
    def valid_payload(self):
        self.user = None

        try:
            username = self.payload['transition_user']
            self.user=User.objects.get(username=username)
        except User.DoesNotExist:
            logger.error("User Doesn't exist")
            return False
        except KeyError:
            pass

        try:
            self.article = Article.objects.get(doi=self.doi)
        except Article.DoesNotExist:
            logger.error("That article doesn't exist")
            return False

        try:
            self.transition = Transition.objects.get(name=self.payload['name'])

            if self.transition not in self.article.possible_transitions().all():
                logger.error("That transition is not legal")
                return False
        except Transition.DoesNotExist:
            logger.error("That transition doesn't exist")
            return False
        except KeyError:
            logger.error("Didn't supply transition name")
            return False
        
        logger.debug("API: legal transition request")
        return True

    def control(self):
        self.article.execute_transition(self.transition, self.user)

    def post(self, request, *args, **kwargs):
        self.doi = kwargs['doi']

        response, fail = self.parse_payload(request.body)
        if fail:
            logger.error("Transition POST failed")
            return response

        self.control()
        return self.response(self.payload)

    # return list of available transitions
    def get(self, request, *args, **kwargs):
        self.doi = kwargs['doi']

        try:
            self.article = Article.objects.get(doi=self.doi)
        except Article.DoesNotExist:
            logger.error("That article doesn't exist")
            return self.error_result("That article doesn't exist")

        transitions = self.article.possible_transitions().all()

        t_names = []
        for t in transitions:
            t_names += [t.name]

        return self.response({"possible_transitions": t_names})
