from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic import ListView, DetailView
from django.views.generic.base import View
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ValidationError
from django.template import RequestContext, Template
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.urlresolvers import reverse
from django import forms
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic.edit import FormView
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.core.servers.basehttp import FileWrapper

import simplejson
import re
import datetime
import mimetypes

from django.contrib.auth.models import Group

import os
import sys
import simplejson
import re
import django_filters
from storages.backends.sftpstorage import SFTPStorage, SFTPStorageFile

import transitionrules

from articleflow.models import Article, ArticleState, State, Transition, Journal, AssignmentRatio, Typesetter
from articleflow.forms import AssignmentForm, ReportsDateRange, FileUpload
from issues.models import Issue, Category
from errors.models import ErrorSet, Error, ERROR_LEVEL, ERROR_SET_SOURCES

import logging
logger = logging.getLogger(__name__)

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
    (6, 'Assigned'),
    (7, 'Typesetter'),
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
        return a.order_by(ColumnOrder.parse_type(type) + 'current_state__progress_index')

    @staticmethod
    def issues(a, type):
        return a.order_by(ColumnOrder.parse_type(type) + 'article_extras__num_issues_total')

    @staticmethod
    def errors(a, type):
        return a.order_by(ColumnOrder.parse_type(type) + 'article_extras__num_errors_total')

    @staticmethod
    def assigned(a, type):
        return a.order_by(ColumnOrder.parse_type(type) + 'current_articlestate__assignee__username')
    
    @staticmethod
    def typesetter(a, type):
        return a.order_by(ColumnOrder.parse_type(type) + 'typesetter__name')
    
ORDER_CHOICES = {
    'DOI': ColumnOrder.doi,
    'PubDate' : ColumnOrder.pubdate,
    'Journal' : ColumnOrder.journal,
    'Issues' : ColumnOrder.issues,
    'Errors' : ColumnOrder.errors,
    'State' : ColumnOrder.state,
    'Assigned' : ColumnOrder.assigned,
    'Typesetter' : ColumnOrder.typesetter,
}


class ArticleFilter(django_filters.FilterSet):
    
    doi_widget = forms.TextInput(attrs={'placeholder': 'pone.0012345'})
    doi = django_filters.CharFilter(name='doi', label='DOI', widget=doi_widget)

    datepicker_widget = forms.DateInput(attrs={'class': 'datepicker'})
    pubdate_gte = django_filters.DateFilter(name='pubdate', label='From', lookup_type='gte', widget=datepicker_widget) 
    pubdate_lte = django_filters.DateFilter(name='pubdate', label='To', lookup_type='lte', widget=datepicker_widget) 

    checkbox_widget = forms.CheckboxSelectMultiple()
    journal = django_filters.ModelMultipleChoiceFilter(name='journal', label='Journal', queryset=Journal.objects.all(), widget=checkbox_widget)
    current_articlestate = django_filters.ModelMultipleChoiceFilter(name='current_state', label='Article state', queryset=State.objects.all(), widget=checkbox_widget)
    current_assignee = django_filters.ModelMultipleChoiceFilter(name='current_articlestate__assignee', label='Assigned', queryset=User.objects.filter(is_active=True).order_by('username'))
    typesetter = django_filters.ModelMultipleChoiceFilter(name='typesetter__name', label='Typesetter', queryset=Typesetter.objects.all(), widget=checkbox_widget)
    
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
            requested_cols = range(0,7) #default columns
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

class ArticleDetailTransitionPanel(View):
    template = Template("{% load transitions %} {% render_article_state_control article user 1 %}")

    def get_context_data(self, request, kwargs):
        ctx = RequestContext(request)
        ctx.update({'article': Article.objects.get(doi=kwargs['doi'])})
        ctx.update({'user': request.user})
        return ctx

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request, kwargs)
        r = self.template.render(context)
        return HttpResponse(r)

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
            user = request.user

            # Make sure user is in appropriate group to make transition
            auth_legal = False

            admin_group = Group.objects.get(name='admin')
            if admin_group in user.groups.all():
                auth_legal = True
            else:
                for group in user.groups.all():
                    if group in transition.allowed_groups.all():
                        auth_legal = True
                        break

            if not auth_legal:
                to_json = {
                    'not_allowed_error': {
                        'allowed_groups': []
                        }
                    }                
                return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')    
            
            # Make sure open errors and issues are in correct state
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

            if transition.file_upload_destination:
                logger.debug("Transition requiring file upload attempted: %s" % transition)

                form_render = render_to_response(
                    'articleflow/fileupload_form.html',
                    {
                        "article": article,
                        "transition": transition,
                        "form": FileUpload(article, transition)
                        },
                    context_instance=RequestContext(request)
                    )
                to_json = {
                    'needs_further_info': {
                        'content': form_render.content
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

class ArticleDetailHistory(View):
    template_name = 'articleflow/article_detail_history.html'

    def get_context_data(self, kwargs):
        ctx = {}
        ctx['article'] = get_object_or_404(Article, doi=kwargs['doi'])
        ctx['states'] = ArticleState.objects.filter(article=ctx['article']).order_by('created')
        return ctx

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(kwargs)
        return render_to_response(self.template_name, context, context_instance=RequestContext(request))

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
    #template_name = '404.html'
    template_name = 'articleflow/help.html'

    def get(self, request, *args, **kwargs):
        context = {}
        return render_to_response(self.template_name, context, context_instance=RequestContext(request))

class ReportsMain(View):
    #template_name = '404.html'
    template_name = 'articleflow/reports/main.html'

    def get(self, request, *args, **kwargs):
        context = {}
        return render_to_response(self.template_name, context, context_instance=RequestContext(request))

class ReportsPCQCCounts(View):
    template_name = 'articleflow/reports/pcqccounts.html'

    @method_decorator(login_required())
    @method_decorator(user_passes_test(lambda u: u.groups.filter(name='management').count()== 1))
    def dispatch(self, request, *args, **kwargs):
        return super(ReportsPCQCCounts, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form, **kwargs):
        data = form.cleaned_data
        # hacky fix for non-inclusive end date on filter
        data['end_date'] = data['end_date'] + datetime.timedelta(days=1)
        
        users = {}
        if data['group'] == '1':
            workers = User.objects.filter(groups__name='production')
        if data['group'] == '2':
            workers = User.objects.filter(groups__name='zyg')
        if data['group'] == '3':
            workers = User.objects.filter(Q(groups__name='production')|Q(groups__name='zyg')).all()

        for w in workers.order_by('username').all():
            users[w.username] = {'user': w}
            logger.debug("Worker: %s" % w.username)

        journals = []
        for j in Journal.objects.all():
            journals += [j.short_name]

        from_transitions = Transition.objects.filter(Q(from_state__name='Ready for QC (CW)')|Q(from_state__name='Urgent QC (CW)')).all()

        for u in users.itervalues():
            u['counts'] = {}

            user_as_base = ArticleState.objects.filter(from_transition_user=u['user']).filter(from_transition__in=from_transitions)
            user_as_base = user_as_base.filter(created__gte=data['start_date']).filter(created__lt=data['end_date'])
            
            for j in Journal.objects.all():
                journal_base = user_as_base.filter(article__journal=j)
                u['counts'][j.short_name] = journal_base.count()
            
            u['actions'] = user_as_base.order_by('created').all()
            
            u['total'] = 0
            for c in u['counts'].itervalues():
                u['total'] += c
    
        journal_totals = {}
        for j in Journal.objects.all():
            journal_totals[j.short_name] = 0
            for u in users.itervalues():
                journal_totals[j.short_name] += u['counts'][j.short_name]
        
        journal_total=0
        for c in journal_totals.itervalues():
            journal_total += c

        return {'users': users,
                'journal_totals': journal_totals,
                'journal_total': journal_total,
                'journals': journals}

    def get_context_data(self,request, *args, **kwargs):
        context = {}
        if self.request.GET:
            form = ReportsDateRange(self.request.GET)
            if form.is_valid():
                return {'results': self.form_valid(form),
                        'form': form}
            else:
                return {'form': form}

        return {'form': ReportsDateRange}

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(kwargs)
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

        

class AssignToMe(View):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            to_json = {
                'error': 'Need to login'
                }
            return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')
        if request.is_ajax():
            article = Article.objects.get(pk=request.POST['article_pk'])
            user = request.user

            # Make sure user is in appropriate group to make assignment
            if not article.current_state.worker_groups.filter(user=user):
                to_json = {
                    'error': "You're not allowed to make this assignment"
                    }
                return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')
            
            # Make sure nobody else grabbed the article
            other_assignee = article.current_articlestate.assignee
            if other_assignee:
                to_json = {
                    'other_assignee': other_assignee.username
                    }
                return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')

            # Make assignment
            article.current_articlestate.assign_user(request.user)

            to_json = {
                'redirect_url': reverse('detail_main', args=[article.doi])
                }
            return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')

class AssignRatiosMain(View):
    template_name = 'articleflow/assign_ratios_main.html'

    def get_context_data(self, kwargs):
        assignment_states = State.objects.filter(auto_assign__gte=2).all()
        return {'assignment_states': assignment_states}

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(kwargs)        
        return render_to_response(self.template_name, context, context_instance=RequestContext(request))
    

class AssignRatios(View):
    template_name = 'articleflow/assign_ratios.html'
    
    def get_context_data(self, kwargs):
        try:
            state = State.objects.get(pk=kwargs['state_pk'])
        except ValueError, State.DoesNotExist:
            raise Http404

        users = state.possible_assignees()
        u_ratios = []

        for u in users:
            try:
                a_r = AssignmentRatio.objects.get(user=u, state=state)
            except AssignmentRatio.DoesNotExist:
                a_r = None
                
            u_ratios += [{'user': u,
                          'assignment_ratio': a_r}]    
                    
        ctx = {
            'state': state,
            'form': AssignmentForm(u_ratios, state.pk)
            }
        
        return ctx

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(kwargs)
        return render_to_response(self.template_name, context, context_instance=RequestContext(request))

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return HttpResponse("You need to log in dummy")
        
        try:
            state = State.objects.get(pk=kwargs['state_pk'])
        except ValueError, State.DoesNotExist:
            raise Http404

        users = state.possible_assignees()
        u_ratios = []

        for u in users:
            try:
                a_r = AssignmentRatio.objects.get(user=u, state=state)
            except AssignmentRatio.DoesNotExist:
                a_r = None
                
            u_ratios += [{'user': u,
                          'assignment_ratio': a_r}]    

        form = AssignmentForm(u_ratios=u_ratios, state_pk=state.pk, data=request.POST)

        if form.is_valid():
            print "request"
            print request.POST
            print "form fields"
            print form.fields

            state = State.objects.get(pk=request.POST['state'])

            for key, val in request.POST.iteritems():
                if key in ('state', 'csrfmiddlewaretoken', 'submit'):
                    continue
                    #pass
                
                print "key: %s" % key
                username = re.search('(?<=user_).*', key).group(0)
                print "username: %s" % username
                user = User.objects.get(username=username)

                a_s, new = AssignmentRatio.objects.get_or_create(user=user, state=state)
                a_s.weight = val
                a_s.save()
                
        else:
            ctx = self.get_context_data(kwargs)
            ctx['form'] = form
            return render_to_response(self.template_name, ctx, context_instance=RequestContext(request))

        ctx = self.get_context_data(kwargs)
        return render_to_response(self.template_name, ctx, context_instance=RequestContext(request))

## SFTP Storage stuff

# had to override a bit of django-storages here
#  it was doing naughty things with StringIOs
class CSFTPStorage(SFTPStorage):
    def _save(self, name, content):
        """Save file via SFTP."""
        path = self._remote_path(name)
        dirname = self._pathmod.dirname(path)
        if not self.exists(dirname):
            self._mkdir(dirname)

        f = self.sftp.open(path, 'wb')
        f.write(content)
        f.close()

        # set file permissions if configured
        if self._file_mode is not None:
            self.sftp.chmod(path, self._file_mode)
        if self._uid or self._gid:
            self._chown(path, uid=self._uid, gid=self._gid)
        return name

def serve_doc_ftp(storage, filename):
    storage_file = SFTPStorageFile(filename, storage, 'r')
    #wrapper = FileWrapper(storage_file.read())
    mime, enc = mimetypes.guess_type(filename, False)
    print "mime: %s" % mime
    try:
        response = HttpResponse(storage_file.read(), content_type=mime)
    except IOError, e:
        raise Http404
    response['Content-Length'] = storage_file.size
    response['Content-Disposition'] = "attachment; filename=%s" % filename
    #storage_file.close()
    return response

def send_file(pathname):
    basename = os.path.basename(pathname)
    mime, enc = mimetypes.guess_type(basename, False)
    logger.debug("Opening file at '%s' for reading." % pathname)
    wrapper = FileWrapper(file(pathname))

    response = HttpResponse(wrapper, content_type=mime)
    response['Content-Length'] = os.path.getsize(pathname)
    response['Content-Disposition'] = "attachment; filename=%s" % basename
    return response

def upload_doc(storage, file_name, file_stream):
    storage_file = SFTPStorageFile(file_name, storage, 'rw')
    storage_file.write(file_stream)
    print storage_file.file.getvalue()
    storage_file.close()

merops_file_schema = {
    'meropsed.doc': {
        'dir_path': '/home/jlabarba/fileserve_test/merops_output/',
        'filename_modifier': '',
        'file_extension': 'doc',
        },
    'meropsed-original.doc': {
        'dir_path': '/home/jlabarba/fileserve_test/merops_output/',
        'filename_modifier': '-original',
        'file_extension': 'doc',
        },
    'meropsed-original.xml': {
        'dir_path': '/home/jlabarba/fileserve_test/merops_output/',
        'filename_modifier': '',
        'file_extension': 'xml',
        },
    'finishxml.doc': {
        'dir_path': '/home/jlabarba/fileserve_test/finishxml_output/',
        'filename_modifier': '-finishxmlcheck-original',
        'file_extension': 'doc',
        },
    'finishxml-original.doc': {
        'dir_path': '/home/jlabarba/fileserve_test/finishxml_output/',
        'filename_modifier': '-finishxmlcheck-original',
        'file_extension': 'doc',
        },
    'finishxml.xml': {
        'dir_path': '/home/jlabarba/fileserve_test/finishxml_output/',
        'filename_modifier': '',
        'file_extension': 'xml',
        },
    }

class ServeArticleDoc(View):
    dir_path = '/home/jlabarba/fileserve_test/' 
    filename_modifier = ''
    file_extension = 'doc'

    def get(self, request, *args, **kwargs):
        try:
            article = Article.objects.get(doi=kwargs['doi'])
        except Article.DoesNotExist, e:
            raise Http404("Couldn't find any article with the doi %s" % kwargs['doi'])

        if kwargs['file_type']:
            try:
                schema_item = merops_file_schema[kwargs['file_type']]
            except KeyError:
                raise Http404("'%s' is not a recognized downloadable merops file type."% kwargs['file_type'])
            self.dir_path = schema_item['dir_path']
            self.filename_modifier = schema_item['filename_modifier']
            self.file_extension = schema_item['file_extension']

        pathname = os.path.join(self.dir_path, "%s%s.%s" % (article.doi, self.filename_modifier, self.file_extension))
        
        try:
            return send_file(pathname)
        except IOError, e:
            raise Http404("Couldn't find that file on disk: %s" % pathname)


    
class FTPMeropsdOrig(View):
    def get(self, request, *args, **kwargs):
        sftp = SFTPStorage()
        #return HttpResponse('fake')
        return serve_doc(sftp, "%s.zip" % kwargs['doi'])

class FTPMeropsUpload(View):
    template_name = 'articleflow/fileupload_form.html'

    def get(self, request, *args, **kwargs):
        form = FileUpload()
        context = {'form': form}
        return render_to_response(self.template_name, context, context_instance=RequestContext(request))

    def post(self, request, *args, **kwargs):
        form = FileUpload(request.POST, request.FILES)
        if form.is_valid():
            ctx = context_instance=RequestContext(request)
            print ctx
            transition = ctx['transition']
            #sftp = CSFTPStorage()
            #print request.FILES
            #upload_doc(sftp, 'upload_test', request.FILES['file'].read())
            
            return HttpResponse("success!")
        context = {'form': form}
        return render_to_response(self.template_name, context, context_instance=RequestContext(request))
