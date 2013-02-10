from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.generic import ListView, DetailView
from django.views.generic.base import View
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.template import RequestContext
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django import forms
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

import simplejson
import re

import django_filters

import transitionrules

from articleflow.models import Article, ArticleState, State, Transition, Journal
from issues.models import Issue, Category
from errors.models import ErrorSet, Error, ERROR_LEVEL, ERROR_SET_SOURCES

def resolve_choice_index(choices, key):
    for choice in choices:
        if key == choice[1]:
            return choice[0]
    return None

COLUMN_CHOICES = (
    (0, 'DOI'),
    (1, 'PubDate'),
    (2, 'Journal'),
    (3, 'Issues'),
    (4, 'Errors'),
    (5, 'State'),
    )

def get_journal_from_doi(doi):
    match = re.match('.*(?=\.)', doi)
    
    if not match:
        raise ValueError('Could not find a journal short_name in doi, %s' % doi)
    short_name = re.match('.*(?=\.)', doi).group(0)
    
    try:
        return Journal.objects.get(short_name=short_name)
    except Journal.DoesNotExist:
        raise ValueError("doi prefix, %s, does not match any known journal" % short_name)

def separate_errors(e):
    if not e:
        return []
    errors_raw = e.strip().splitlines(False)
    
    errors=[]
    for error in errors_raw:
        error_tuple = (error, 1)
        print "Raw: %s" % error
        for i, level in ERROR_LEVEL:
            
            p = re.compile('(?<=%s:).*' % level, re.IGNORECASE)
            m = p.search(error) 
            if m:
                print "Match: %s" % m.group(0)
                error_tuple = (m.group(0).strip(), i)
                break

        errors += [error_tuple]
    
    return errors

class ColumnOrder():
    @staticmethod
    def parse_type(type):
        if type == 'asc':
            return ''
        elif type == 'desc':
            return '-'
        raise ValueError

    @staticmethod
    def pubdate(a, type):
        return a.order_by(ColumnOrder.parse_type(type) + 'pubdate')

    @staticmethod
    def doi(a, type):
        return a.order_by(ColumnOrder.parse_type(type) + 'doi')

    @staticmethod
    def journal(a, type):
        return a.order_by(ColumnOrder.parse_type(type) + 'journal__short_name')

    @staticmethod
    def state(a, type):
        return a.order_by(ColumnOrder.parse_type(type) + 'current_state')

    @staticmethod
    def issues(a, type):
        return a.order_by(ColumnOrder.parse_type(type) + 'article_extras__num_issues_total')

    @staticmethod
    def errors(a, type):
        return a.order_by(ColumnOrder.parse_type(type) + 'article_extras__num_errors_total')
    
ORDER_CHOICES = {
    'DOI': ColumnOrder.doi,
    'PubDate' : ColumnOrder.pubdate,
    'Journal' : ColumnOrder.journal,
    'Issues' : ColumnOrder.issues,
    'Errors' : ColumnOrder.errors,
    'State' : ColumnOrder.state,
}


class ArticleFilter(django_filters.FilterSet):
    
    doi = django_filters.CharFilter(name='doi', label='DOI')

    datepicker_widget = forms.DateInput(attrs={'class': 'datepicker'})
    pubdate_gte = django_filters.DateFilter(name='pubdate', label='Pubdate on or after', lookup_type='gte', widget=datepicker_widget) 
    pubdate_lte = django_filters.DateFilter(name='pubdate', label='Pubdate on or before', lookup_type='lte', widget=datepicker_widget) 

    journal = django_filters.ModelMultipleChoiceFilter(name='journal', label='Journal', queryset=Journal.objects.all())
    current_articlestate = django_filters.ModelMultipleChoiceFilter(name='current_state', label='Article state', queryset=State.objects.all())
    
    class Meta:
        model = Article
        fields = []

class ArticleGrid(View):    
    template_name = 'articleflow/grid.html'

    def get_results_per_page(self):
        if not self.request.GET.getlist('page_size'):
            return 50
        else:
            return self.request.GET.getlist('page_size')[0]

    def get_selected_cols(self):
        if not self.request.GET.getlist('cols'):
            requested_cols = range(0,6) #default columns
        else:
            requested_cols = [0] #make sure DOI is always included
            requested_cols += self.request.GET.getlist('cols')
        return requested_cols

    def get_selected_cols_names(self, requested_cols):
        name_list = []
        for col in requested_cols:
            name_list.append(COLUMN_CHOICES[int(col)][1])
        return name_list
        
    def get_context_data(self, **kwargs):
        #context = super(ArticleGrid, self).get_context_data(**kwargs)
        if self.request.GET:
            print "QUERY DATA!"
            print self.request.GET
        context = {}
        
        raw_list = ArticleFilter(self.request.GET, queryset=Article.objects.all())

        # Order!
        order_col = self.request.GET.getlist('order_col')
        order_mode = self.request.GET.getlist('order_mode')
        print order_col
        if not order_col:
            qs = ColumnOrder.pubdate(raw_list.qs, 'asc')
        else:
            try:
                fn = ORDER_CHOICES[order_col[0]]
                qs = fn(raw_list.qs, order_mode[0] or '')
            except KeyError:
                print "Can't order by that"
                qs = ColumnOrder.pubdate(raw_list.qs, 'asc')



        # Paginate!
        paginator = Paginator(qs, self.get_results_per_page())
        get_page_num = self.request.GET.get('page')

        try:
            article_page = paginator.page(get_page_num)
        except PageNotAnInteger:
            article_page = paginator.page(1)
        except EmptyPage:
            article_page = paginator.page(paginator.num_pages)

        # construct urls for next and last page
        r_query = self.request.GET.copy()
        if article_page.has_next():
            r_query['page'] = article_page.next_page_number()
            context['next_page_qs'] = r_query.urlencode()
        r_query = self.request.GET.copy()
        if article_page.has_previous():
            r_query['page'] = article_page.previous_page_number()
            print r_query
            context['previous_page_qs'] = r_query.urlencode()
        

        context['article_list'] = article_page
        context['total_articles'] = sum (1 for article in raw_list)
        context['pagination'] = article_page
        context['filter_form'] = raw_list.form
        requested_cols = self.get_selected_cols()
        context['requested_cols'] = self.get_selected_cols_names(requested_cols)
        context['base_qs'] = self.request.GET.urlencode()
        context['error_level'] = ERROR_LEVEL
        
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        context['column_choices'] = COLUMN_CHOICES[1:]
        
        return render_to_response(self.template_name, context, context_instance=RequestContext(request))

class ArticleDetailMain(View):
    
    template_name = 'articleflow/article_detail_main.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(kwargs)
        return render_to_response(self.template_name, context, context_instance=RequestContext(request))

    def get_context_data(self, kwargs):
        article = Article.objects.get(doi=kwargs['doi'])
        context = ({
                'article': article,
            })
        return context

class ArticleDetailTransition(View):

    template_name = 'articleflow/possible_transitions.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(kwargs)
        return render_to_response(self.template_name, context, context_instance=RequestContext(request))

    def get_context_data(self, kwargs):
        article = Article.objects.get(doi=kwargs['doi'])
        transitions = article.possible_transitions().select_related()
        context = ({
                'article': article,
                'transitions': transitions,
            })
        return context

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            to_json = {
                'error': 'Need to login'
                }
            return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')
        if request.is_ajax():
            article = Article.objects.get(pk=request.POST['article_pk'])
            transition = Transition.objects.get(pk=request.POST['requested_transition_pk'])
            # @TODO, fix this shit!
            user = User.objects.get(pk=1)

            if transition.disallow_open_items:
                open_items = transitionrules.article_count_open_items(article)
                if (open_items['open_issues'] > 0 or open_items['open_errors'] > 0):
                    to_json = {
                        'open_item_error': {
                            'open_issues': open_items['open_issues'],
                            'open_errors': open_items['open_errors']
                            }
                        }
                    return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')    
            success = article.execute_transition(transition, user)
            #context = self.get_context_data(kwargs)
            print "success?"
            print success

            if success:    
                to_json = {
                    'redirect_url': request.META.get('HTTP_REFERER', reverse('home'))
                    }
                return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')
            else:
                to_json = {
                    'error': 'State transition failed'
                    }
                return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')

            #return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('home')))
        #return render_to_response(self.template_name, context, context_instance=RequestContext(request))

class ArticleDetailIssues(View):

    template_name = 'articleflow/article_detail_issues.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(kwargs)
        return render_to_response(self.template_name, context, context_instance=RequestContext(request))

    def get_context_data(self, kwargs):
        article = Article.objects.get(doi=kwargs['doi'])
        issues = Issue.objects.filter(article=article).select_related()
        context = ({
                'issues': issues,
                'article': article
                })
        return context


class Help(View):
    template_name = '404.html'
    #template_name = 'articleflow/help.html'

    def get(self, request, *args, **kwargs):
        context = {}
        return render_to_response(self.template_name, context, context_instance=RequestContext(request))


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
        print json_str
        try:
            self.payload = simplejson.loads(json_str)
        except:
            print "Couldn't parse json"
            return (self.error_response("Unable to parse json message"), True)

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
        print self.payload
        self.payload['doi'] = self.doi

        try:
            self.payload['journal']=get_journal_from_doi(self.payload['doi']).pk
            print "Journal: %s" % self.payload['journal']
        except ValueError:
            print "Can't resolve journal"
            return False

        try:
            print "Validating date"
            match = re.match('[0-9]{4}-[0-9]{2}-[0-9]{2}$', self.payload['pubdate'])
            print match
            if not match:
                print "Incorrect pubdate format"
                return False
        except KeyError:
            pass

        try:
            requested_state = self.payload['state']
            state=State.objects.get(name=requested_state)
        except State.DoesNotExist:
            print "Nonexistant state"
            return False
        except KeyError:
            pass

        try:
            username = self.payload['state_change_user']
            user=User.objects.get(username=username)
        except User.DoesNotExist:
            print "User Doesn't exist"
            return False
        except KeyError:
            pass

        return True

    def control(self):
        print "start control"
        a, new = Article.objects.get_or_create(doi=self.get_val('doi'),
                                               journal=Journal.objects.get(pk=self.get_val('journal')))
        print "New article? %s" % new

        if self.get_val('pubdate'):
            a.pubdate=self.get_val('pubdate')
        if self.get_val('md5'):
            a.md5=self.get_val('md5')
        if self.get_val('si_guid'):
            a.si_guid=self.get_val('si_guid')

        print "Journal: %s" % self.payload['journal']
        a.journal=Journal.objects.get(pk=self.get_val('journal'))
                                          
        print "New article? %s" % new
        a.save()

        requested_state = self.get_val('state')
        if requested_state:
            if a.current_state.name != requested_state:
                s = ArticleState(article=a,
                                 state=State.objects.get(name=requested_state)
                                 )
                if self.get_val('state_change_user'):
                    s.from_transition_user = User.objects.get(username=self.get_val('state_change_user')) 

                s.save()
        return self.payload

    def put(self, request, *args, **kwargs):
        print "start put"
        self.doi = kwargs['doi']
        response, fail = self.parse_payload(request.body)
        if fail:
            return response
        print self.payload
        print "pubdate: %s" % self.get_val('pubdate')

        # make change
        response_dict = self.control()

        return self.get(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        print kwargs
        print kwargs['doi']
        try:
            a = Article.objects.get(doi=kwargs['doi'])
        except Article.DoesNotExist:
            return self.error_response('Article does not exist')
        
        pubdate_str = None
        if a.pubdate:
            pubdate_str = a.pubdate.strftime("%Y-%m-%d")

        a_dict = {'doi': a.doi,
                  'pubdate': pubdate_str,
                  'state': a.current_state.name,
                  'si_guid': a.si_guid,
                  'md5': a.md5,
                  }

        return self.response(a_dict)
                                   

class TransactionErrorset(BaseTransaction):
    def valid_payload(self):
        print self.payload

        try:
            self.article = Article.objects.get(doi=self.doi)
        except Article.DoesNotExist:
            print "That article doesn't exist"
            return False

        try:
            self.source_i = resolve_choice_index(ERROR_SET_SOURCES, self.payload['source'])
            if not self.source_i:
                print "Source doesn't exist"
                return False
        except KeyError:
            print "Didn't supply source"
            return False

        try:
            self.payload['errors']
        except KeyError:
            print "Didn't supply errors"
            return False

        return True
        
    def control(self):
        print "start control"
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
        print "REQUEST BODY:"
        response, fail = self.parse_payload(request.body)
        if fail:
            return response

        self.control()
        return self.response(self.payload)


    def get(self, request, *args, **kwargs):
        return self.error_response("Not Implemented")

class TransactionTransition(BaseTransaction):
    def valid_payload(self):
        print self.payload

        try:
            username = self.payload['transition_user']
            self.user=User.objects.get(username=username)
        except User.DoesNotExist:
            print "User Doesn't exist"
            return False
        except KeyError:
            pass

        try:
            self.article = Article.objects.get(doi=self.doi)
        except Article.DoesNotExist:
            print "That article doesn't exist"
            return False

        try:
            self.transition = Transition.objects.get(name=self.payload['name'])

            if self.transition not in self.article.possible_transitions().all():
                print "That transition is not legal"
                return False
        except Transition.DoesNotExist:
            print "That transition doesn't exist"
            return False
        except KeyError:
            print "Didn't supply transition name"
            return False
        
        return True

    def control(self):
        self.article.execute_transition(self.transition, self.user)

    def post(self, request, *args, **kwargs):
        self.doi = kwargs['doi']

        response, fail = self.parse_payload(request.body)
        if fail:
            return response

        self.control()
        return self.response(self.payload)

    # return list of available transitions
    def get(self, request, *args, **kwargs):
        self.doi = kwargs['doi']

        try:
            self.article = Article.objects.get(doi=self.doi)
        except Article.DoesNotExist:
            print "That article doesn't exist"
            return self.error_result("That article doesn't exist")

        transitions = self.article.possible_transitions().all()

        t_names = []
        for t in transitions:
            t_names += [t.name]

        return self.response({"possible_transitions": t_names})

        
