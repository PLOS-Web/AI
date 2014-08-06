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
import glob
import datetime
import mimetypes

from django.contrib.auth.models import Group

import os
import subprocess
import sys
import simplejson
import re
import django_filters

import rhyno
import transitionrules

from ai import settings
from ai import ambra_settings
from articleflow.models import Article, ArticleState, ArticleType, State, Transition, Journal, AssignmentRatio, AssignmentHistory, Typesetter, reassign_article, toUTCc
from articleflow.forms import AssignmentForm, ReportsDateRange, ReportsMeropsForm, ReportsCorrectiontoReadytoPublishForm, FileUpload, AssignArticleForm
from issues.models import Issue, Category
from errors.models import ErrorSet, Error, ERROR_LEVEL, ERROR_SET_SOURCES

# other views
from views_api import *

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
    (6, 'State Started'),
    (7, 'Assigned'),
    (8, 'Typesetter'),
    (9, 'Article Type')
    )

DEFAULT_COLUMNS = [0,1,3,4,5,6,7,9]

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
            
            p = re.compile('(?<=^%s:).*' % level, re.IGNORECASE)
            m = p.search(error) 
            if m:
                logger.debug("Match: %s" % m.group(0))
                error_tuple = (m.group(0).strip(), i)
                break

        errors += [error_tuple]
    
    return errors

def time_between_states(previous, current):
    """
    Accepts to datetime objects, and returns
    a string of the time difference between the two.
    """
    t = current - previous
    days, remainder = divmod(t.seconds, 86400)
    hours, min_rem = divmod(remainder, 3600)
    minutes, seconds = divmod(min_rem, 60)
    return str(days)+" days, "+str(hours)+' hrs, '+str(minutes)+' mins, '+str(seconds)+' secs'


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

    @staticmethod
    def article_type(a, type):
        return a.order_by(ColumnOrder.parse_type(type) + 'article_type__name')

    @staticmethod
    def state_started(a, type):
        return a.order_by(ColumnOrder.parse_type(type) + 'current_articlestate__created')
    
ORDER_CHOICES = {
    'DOI': ColumnOrder.doi,
    'PubDate': ColumnOrder.pubdate,
    'Journal': ColumnOrder.journal,
    'Issues': ColumnOrder.issues,
    'Errors': ColumnOrder.errors,
    'State': ColumnOrder.state,
    'State Started': ColumnOrder.state_started,
    'Assigned': ColumnOrder.assigned,
    'Typesetter': ColumnOrder.typesetter,
    'Article Type': ColumnOrder.article_type,
}


class ArticleFilter(django_filters.FilterSet):
    
    doi_widget = forms.TextInput(attrs={'placeholder': 'pone.0012345'})
    doi = django_filters.CharFilter(name='doi', label='DOI', widget=doi_widget)

    datepicker_widget = forms.DateInput(attrs={'class': 'datepicker', 'data-time-icon': 'icon_time'})
    datetimepicker_widget = forms.DateTimeInput(attrs={'class': 'datetimepicker'})
    pubdate_gte = django_filters.DateFilter(name='pubdate', label='Pubdate from', lookup_type='gte', widget=datepicker_widget) 
    pubdate_lte = django_filters.DateFilter(name='pubdate', label='Pubdate to', lookup_type='lte', widget=datepicker_widget) 

    checkbox_widget = forms.CheckboxSelectMultiple()
    journal = django_filters.ModelMultipleChoiceFilter(name='journal', label='Journal', queryset=Journal.objects.all(), widget=checkbox_widget)
    current_articlestate = django_filters.ModelMultipleChoiceFilter(name='current_state', label='Article state', queryset=State.objects.all(), widget=checkbox_widget)
    state_started_gte = django_filters.DateTimeFilter(name='current_articlestate__created', label='State started from', lookup_type='gte', widget=datepicker_widget) 
    state_stated_lte = django_filters.DateTimeFilter(name='current_articlestate__created', label='State started to', lookup_type='lte', widget=datepicker_widget)
    current_assignee = django_filters.ModelMultipleChoiceFilter(name='current_articlestate__assignee', label='Assigned', queryset=User.objects.filter(is_active=True).order_by('username'))
    typesetter = django_filters.ModelMultipleChoiceFilter(name='typesetter__name', label='Typesetter', queryset=Typesetter.objects.all(), widget=checkbox_widget)
    article_type = django_filters.ModelMultipleChoiceFilter(name='article_type__name', label='Article Type', queryset=ArticleType.objects.all(), widget=checkbox_widget)

    
    class Meta:
        model = Article
        fields = []

class ArticleGridSearch(View):    
    template_name = 'articleflow/grid_search_view.html'
    
    def get_context_data(self, **kwargs):
        context = {}
        raw_list = ArticleFilter(self.request.GET, queryset=Article.objects.all())
        context['filter_form'] = raw_list.form
        return context
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return render_to_response(self.template_name, context, context_instance=RequestContext(request))
        

class ArticleGrid(View):    
    template_name = 'articleflow/grid.html'

    def get_results_per_page(self):
        if not self.request.GET.getlist('page_size'):
            return 50
        else:
            return self.request.GET.getlist('page_size')[0]

    def get_selected_cols(self):
        if not self.request.GET.getlist('cols'):
            requested_cols = DEFAULT_COLUMNS #default columns
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
        context = {}
        
        raw_list = ArticleFilter(self.request.GET, queryset=Article.objects.all())

        # Order!
        order_col = self.request.GET.getlist('order_col')
        order_mode = self.request.GET.getlist('order_mode')
        if not order_col:
            qs = ColumnOrder.pubdate(raw_list.qs, 'asc')
        else:
            try:
                fn = ORDER_CHOICES[order_col[0]]
                qs = fn(raw_list.qs, order_mode[0] or '')
            except KeyError:
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
        article = get_object_or_404(Article, doi=kwargs['doi'])
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

class ArticleDetailTransitionUpload(View):

    def handle_uploaded_file(self, f, destinations, filename):
        logger.debug("Handling file upload for %s" % filename)
        dests = destinations.split(' ')
        for dest in dests:
            if not os.path.exists(dest):
                logger.error("File upload destination path, %s, does not exist. skipping." % dest)
                continue
            destination_pathname = os.path.join(dest, filename)
            logger.debug("Writing uploaded file to %s" % destination_pathname)
            with open(destination_pathname, 'wb+') as destination:
                for chunk in f.chunks():
                    destination.write(chunk)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            to_json = {
                'error': 'Need to login'
                }
            return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')
        article = get_object_or_404(Article, pk=request.POST['article_pk'])
        transition = get_object_or_404(Transition, pk=request.POST['requested_transition_pk'])
        form = FileUpload(article, transition, reverse('detail_transition_upload', args=(article.doi,)), request.POST, request.FILES)
        if form.is_valid():
            if transition in article.possible_transitions():
                logger.debug("Handling uploaded file: %s . . ." % request.FILES['file'].name)
                f_name, extension = os.path.splitext(request.FILES['file'].name)
                self.handle_uploaded_file(request.FILES['file'], transition.file_upload_destination, "%s%s" % (article.doi, extension))
                article.execute_transition(transition, request.user)
                return HttpResponseRedirect(reverse('detail_main', args=(article.doi,)))

        return HttpResponse("Form error: %s Please tell your administrator, Jack LaBarba <jlabarba@plos.org>" % form.errors)

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
                        "form": FileUpload(article, transition, reverse('detail_transition_upload', args=(article.doi,)))
                        },
                    context_instance=RequestContext(request)
                    )
                logger.debug(form_render.content)
                to_json = {
                    'needs_further_info': {
                        'content': form_render.content
                        }
                    }
                return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')                
            success = article.execute_transition(transition, user)
            #context = self.get_context_data(kwargs)

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
        print data
        # hacky fix for non-inclusive end date on filter
        data['end_date'] = data['end_date'] + datetime.timedelta(days=1)
        
        users = {}
        if data['group'] == '1':
            workers = User.objects.filter(groups__name='production')
        if data['group'] == '2':
            workers = User.objects.filter(groups__name='zyg')
        if data['group'] == '3':
            workers = User.objects.filter(groups__name='staninfo QC outsourcers')
        if data['group'] == '4':
            workers = User.objects.filter(Q(groups__name='production')|Q(groups__name='zyg')|Q(groups__name='staninfo QC outsourcers')).all()

        for w in workers.order_by('username').all():
            users[w.username] = {'user': w}
            logger.debug("Worker: %s" % w.username)

        journals = []
        for j in Journal.objects.all():
            journals += [j.short_name]

        if int(data['typesetter']) == 1:
            from_transitions = Transition.objects.filter(Q(from_state__name='Ready for QC (CW)')|Q(from_state__name='Urgent QC (CW)')).all()
        elif int(data['typesetter']) == 2:
            from_transitions = Transition.objects.filter(Q(from_state__unique_name='ready_for_qc_merops')|Q(from_state__unique_name='urgent_qc_merops')).all()
        elif int(data['typesetter']) == 3:
            from_transitions = Transition.objects.filter(Q(from_state__unique_name='ready_for_qc_merops')|Q(from_state__unique_name='urgent_qc_merops')|Q(from_state__unique_name='ready_for_qc_cw')|Q(from_state__unique_name='urgent_qc_cw')).all()
        elif int(data['typesetter']) == 4:
            from_transitions = Transition.objects.filter(from_state__unique_name='prepare_manuscript').all()

        arts =[]
        total_papers_with_issues = 0
        total_issues = 0

        for u in users.itervalues():
            u['counts'] = {}

            user_as_base = ArticleState.objects.filter(from_transition_user=u['user']).filter(from_transition__in=from_transitions)
            user_as_base = user_as_base.filter(created__gte=data['start_date']).filter(created__lt=data['end_date'])
            
            for j in Journal.objects.all():
                journal_base = user_as_base.filter(article__journal=j)
                u['counts'][j.short_name] = journal_base.count()
            
            u['actions'] = user_as_base.order_by('created').all()

            u['actions_dict'] = {}
            for art in user_as_base.order_by('created').all():
                for a in ArticleState.objects.filter(article=art.article):
                    if a.state.name == art.from_transition.from_state.name:
                        u['actions_dict'][a] = {'start_time': art.created,
                                                'end_time': a.created,
                                                'total_time': time_between_states(a.created, art.created),
                                                'state': art.state.name, 'poop': 'poop'}
            print "actions_dict", u['user'], u['actions_dict']
            
            u['total'] = 0
            for c in u['counts'].itervalues():
                u['total'] += c

            # Let's try and get some totals. Add the articles to a list we'll use outside the loop.
            # Only add them if they don't exist already (no dupes)
            for art in user_as_base:
                if art.article not in arts:
                    arts.append(art.article)
    
        for a in arts:
            if a.issues.count() > 0:
                total_issues += a.issues.count()
                total_papers_with_issues += 1

    
        journal_totals = {}
        for j in Journal.objects.all():
            journal_totals[j.short_name] = 0
            for u in users.itervalues():
                journal_totals[j.short_name] += u['counts'][j.short_name]
        
        journal_total=0
        for c in journal_totals.itervalues():
            journal_total += c

        totes = {'Total Papers': journal_total,
                 'Total Papers with Issues': total_papers_with_issues,
                 'Total # of Issues': total_issues}

        return {'users': users,
                'journal_totals': journal_totals,
                'journal_total': journal_total,
                'journals': journals,
                'totes': totes}

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
        
class ReportMeropsCounts(View):
    template_name = 'articleflow/reports/meropscounts.html'

    @method_decorator(login_required())
    @method_decorator(user_passes_test(lambda u: u.groups.filter(name='management').count()== 1))
    def dispatch(self, request, *args, **kwargs):
        return super(ReportMeropsCounts, self).dispatch(request, *args, **kwargs)  

    def form_valid(self, form):
        data = form.cleaned_data

        # hacky fix for non-inclusive end date on filter
        data['end_date'] = data['end_date'] + datetime.timedelta(days=1)

        article_objs = Article.objects.filter(current_articlestate__state__unique_name='published_live').filter(pubdate__gte=data['start_date']).filter(pubdate__lt=data['end_date']).order_by('pubdate')


        if data['typesetter'] == '1':
            article_objs = article_objs.filter(~Q(typesetter__name='Merops'))
        elif data['typesetter'] == '2':
            article_objs = article_objs.filter(typesetter__name='Merops')
        elif data['typesetter'] == '3':
            pass 

        if not article_objs: return {}
        articles = []
        ingested_state = State.objects.get(unique_name='ingested')
        pulled_state = State.objects.get(unique_name='pulled')
        automatic_threshold = datetime.timedelta(minutes=30)

        total_count = 0
        no_errors_count = 0
        no_issues_count = 0
        automated_ingest_count = 0
        passed_cleanly_count = 0
        
        for a in article_objs:
            total_count += 1
            art = {'article': a}
            try:
                latest_errorset = ErrorSet.objects.filter(article=a).latest('created')
                art['no_errors'] = (latest_errorset.errors.filter(level__lt=3).count() == 0)
            except ErrorSet.DoesNotExist, e:
                art['no_errors'] = False

            if art['no_errors']: no_errors_count += 1

            issues = a.issues
            art['no_issues'] = (issues.count() == 0 or (issues.count() == 1 and issues.get().description.strip().lower() == 'ok')) 
            if art['no_issues']: no_issues_count += 1

            try:
                latest_ingest = ArticleState.objects.filter(article=a, state=ingested_state).latest('created')
                latest_pull = ArticleState.objects.filter(article=a, state=pulled_state).latest('created')
                art['automated_ingest'] = (latest_ingest.created < latest_pull.created + automatic_threshold)
                
            except ArticleState.DoesNotExist, e:
                art['automated_ingest'] = False

            if art['automated_ingest']: automated_ingest_count += 1
            if (art['no_issues'] & art['no_errors'] & art['automated_ingest']): passed_cleanly_count += 1

            articles += [art]

        return {'articles': articles,
                'total_count': total_count,
                'no_errors_count': no_errors_count,
                'no_errors_count_percent': no_errors_count/float(total_count)*100,
                'no_issues_count': no_issues_count,
                'no_issues_count_percent': no_issues_count/float(total_count)*100,
                'automated_ingest_count': automated_ingest_count,
                'automated_ingest_count_percent': automated_ingest_count/float(total_count)*100,
                'passed_cleanly_count': passed_cleanly_count,
                'passed_cleanly_percent': passed_cleanly_count/float(total_count)*100
                }

    def get_context_data(self,request, *args, **kwargs):
        context = {}
        if self.request.GET:
            form = ReportsMeropsForm(self.request.GET)
            if form.is_valid():
                print "FORM IS VALID"
                return {'results': self.form_valid(form),
                        'form': form}
            else:
                print "FORM NOT VALID"
                return {'form': form}

        return {'form': ReportsMeropsForm}

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(kwargs)
        return render_to_response(self.template_name, context, context_instance=RequestContext(request))

class WebCxnsReport(View):
    template_name = 'articleflow/reports/webcxns.html'

    @method_decorator(login_required())
    @method_decorator(user_passes_test(lambda u: u.groups.filter(name='management').count()== 1))
    def dispatch(self, request, *args, **kwargs):
        return super(WebCxnsReport, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        data=form.cleaned_data

        # hacky fix for non-inclusive end date on filter
        end_date_end = data['end_date'] + datetime.timedelta(days=1)
        start_date_begin = data['start_date']

        # Create acceptable typesetter names list
        if data['typesetter'] == '1':
            typesetters = ["CW"]
        elif data['typesetter'] == '2':
            typesetters = ["Merops"]
        elif data['typesetter'] == '3':
            typesetters = ["CW", "Merops"]

        #Base query
        ready_to_pub_objs = ArticleState.objects.filter(state__name="Ready to Publish").filter(created__gte=start_date_begin).filter(created__lte=end_date_end)
        
        # Filter for Ready to Publish articles by requested Group(s)
        if data['group'] == '1': #PLOS
            ready_to_pub_objs = ready_to_pub_objs.filter(from_transition_user__groups__name="web")
        elif data['group'] == '2': #Stan
            ready_to_pub_objs = ready_to_pub_objs.filter(from_transition_user__groups__name="web corrections outsourcers")
        elif data['group'] == '3': #Both
            ready_to_pub_objs = ready_to_pub_objs.filter(Q(from_transition_user__groups__name="web corrections outsourcers")|Q(from_transition_user__groups__name="web")).all()
        
        ready_to_pub_dict = {}
        # For each article in list of ready to pub state, filter previous ArticleState info
        for art in ready_to_pub_objs:
            for a in ArticleState.objects.filter(article=art.article):#.filter(created__gte=cxn_date_begin).filter(created__lte=cxn_date_end):

                if a.state.name == art.from_transition.from_state.name and a.article.typesetter.name in typesetters:
                    ready_to_pub_dict[art.article] = {"ready_to_pub": art.state.name, 
                                                    "ready_to_pub_created": art.created, 
                                                    "cxn_state": a.state.name, 
                                                    "cxn_state_created": a.created, 
                                                    "user": art.from_transition_user, 
                                                    "issues": str(a.article.issues.count())}
                    
                    ready_to_pub_dict[art.article]['total_time'] = time_between_states(a.created, art.created)

        if len(ready_to_pub_dict) == 0:
            return {}

        return {'articles': ready_to_pub_dict}


    def get_context_data(self,request, *args, **kwargs):
        context = {}
        if self.request.GET:
            form = ReportsCorrectiontoReadytoPublishForm(self.request.GET)
            if form.is_valid():
                return {'results': self.form_valid(form),
                        'form': form}
            else:
                return {'form': form}

        return {'form': ReportsCorrectiontoReadytoPublishForm}

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(kwargs)
        return render_to_response(self.template_name, context, context_instance=RequestContext(request))

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

class AssignArticle(View):
    template_name = 'articleflow/assign_article_form.html'

    def get_context_data(self, *args, **kwargs):
        a = get_object_or_404(Article, doi=kwargs['doi'])
        form = AssignArticleForm()
        ctx = {
            'form': form
            }
        return ctx

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(*args, **kwargs)
        return render_to_response(self.template_name, context, context_instance=RequestContext(request))

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return HttpResponse("You need to log in dummy")
        a = get_object_or_404(Article, doi=kwargs['doi'])
        form = AssignArticleForm(article=a, data = request.POST)
        if form.is_valid():
            f_data = form.cleaned_data
            user = get_object_or_404(User, username=f_data['username'])
            reassign_article(a, user, from_transition_user=request.user)
            to_json = {
                'status': 0,
                'assignee': a.current_articlestate.assignee.username,
                }
            logger.debug("%s: form used to update assignee. response: %s" % (a.doi, simplejson.dumps(to_json)))
            return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')
        to_json = {
            'status': 1,
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
                

            midnight = toUTCc(datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0))

            assignments = AssignmentHistory.objects.filter(user=u, article_state__state=state, created__gte=midnight).count()
                
            u_ratios += [{'user': u,
                          'assignment_ratio': a_r,
                          'assignments': assignments}]    
                    
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

            midnight = toUTCc(datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0))

            assignments = AssignmentHistory.objects.filter(user=u, article_state__state=state, created__gte=midnight).count()
                
            u_ratios += [{'user': u,
                          'assignment_ratio': a_r,
                          'assignments': assignments}]    

        form = AssignmentForm(u_ratios=u_ratios, state_pk=state.pk, data=request.POST)

        if form.is_valid():

            state = State.objects.get(pk=request.POST['state'])

            for key, val in request.POST.iteritems():
                if key in ('state', 'csrfmiddlewaretoken', 'submit'):
                    continue
                    #pass
                
                username = re.search('(?<=user_).*', key).group(0)
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

def send_file(pathname, attachment_name=None):
    basename = os.path.basename(pathname)
    if not attachment_name:
        attachment_name = basename
    mime, enc = mimetypes.guess_type(basename, False)
    file_name = glob.glob(pathname)
    if not file_name:
        raise IOError()
    logger.debug("Opening file at '%s' for reading." % file_name[0])
    wrapper = FileWrapper(file(file_name[0]))
    mime, enc = mimetypes.guess_type(file_name[0], False)
    logger.debug("%s mimetype: %s, encoding: %s" % (file_name[0], mime, enc))
    throwaway, extension = os.path.splitext(file_name[0])

    response = HttpResponse(wrapper, content_type=mime)
    response['Content-Length'] = os.path.getsize(file_name[0])
    response['Content-Disposition'] = "attachment; filename=%s%s" % (attachment_name, extension)
    return response

def upload_doc(storage, file_name, file_stream):
    storage_file = SFTPStorageFile(file_name, storage, 'rw')
    storage_file.write(file_stream)
    storage_file.close()

def find_highest_file_version_number(directory, basename):
    angry_prog = re.compile("(?<=\()[0-9]*(?=\))")
    def angry_search(r, n):
        s = r.search(n)
        if s:
            return s.group()
        return None
    
    files = [os.path.basename(f) for f in glob.glob(os.path.join(directory, basename) + "*")]
    if not files:
        raise ValueError("File with that basename doesn't exist")
    numbers = map(lambda x: angry_search(angry_prog, x), files)
    return max(numbers)

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
                schema_item = settings.MEROPS_FILE_SCHEMA[kwargs['file_type']]
            except KeyError:
                raise Http404("'%s' is not a recognized downloadable merops file type."% kwargs['file_type'])
            self.dir_path = schema_item['dir_path']
            self.filename_modifier = schema_item['filename_modifier']
            self.file_extension = schema_item['file_extension']
            try:
                self.version_number = find_highest_file_version_number(self.dir_path, article.doi)
            except ValueError, e:
                logger.error(e)
                raise Http404()
            if self.version_number:
                self.version_number = "(%s)" % self.version_number
            else:
                self.version_number = ""
            
        pathname = os.path.join(self.dir_path, "%s%s%s.%s" % (article.doi, self.version_number, self.filename_modifier, self.file_extension))
        
        try:
            return send_file(pathname, "%s%s" % (article.doi, self.filename_modifier))
        except IOError, e:
            raise Http404(":( I can't find that file.  This likely means that the associated process in merops hasn't been completed.  If you think this 404 message is in error, please contact your admin.")

class HandleCorrectionsDoc(View):
    template_name = 'articleflow/corrections_upload_form.html'

    def handle_uploaded_file(self, f, destinations, filename):
        logger.debug("Handling file upload for %s" % filename)
        dests = destinations.split(' ')
        for dest in dests:
            if not os.path.exists(dest):
                logger.error("File upload destination path, %s, does not exist. skipping." % dest)
                continue
            destination_pathname = os.path.join(dest, filename)
            logger.debug("Writing uploaded file to %s" % destination_pathname)
            with open(destination_pathname, 'wb+') as destination:
                for chunk in f.chunks():
                    destination.write(chunk)
    
    def get(self, request, *args, **kwargs):
        print(kwargs)
        try:
            article = Article.objects.get(doi=kwargs['doi'])
        except Article.DoesNotExist, e:

            raise Http404("Couldn't find any article with the doi %s" % kwargs['doi'])

        source = request.GET.get('source', None)
        logger.debug("source: %s" % source)

        if source == 'ingestible':
            filepath = os.path.join(ambra_settings.AMBRA_INGESTION_QUEUE, "%s.zip" % article.doi)
        elif source == 'ingested':
            filepath = os.path.join(ambra_settings.AMBRA_INGESTED, "%s.zip" % article.doi)
        else:
            logger.error("Unknown or missing source query parameter: %s" % source)
            raise Http404("Unknown or missing source query parameter.")

        if not os.path.exists(filepath):
            logger.error("I could not find a file at %s" % filepath)
            raise Http404("I could not find a file at %s" % filepath)

        return send_file(filepath, article.doi)

    def post(self, request, *args, **kwargs):
        print(kwargs)
        if not request.user.is_authenticated():
            to_json = {
                'error': 'Need to login'
                }
            return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')
        article = get_object_or_404(Article, pk=request.POST['article_pk'])
        form = FileUpload(article, None, reverse('corrections_file', args=(article.doi,)), request.POST, request.FILES)
        if form.is_valid():
            logger.debug("Handling uploaded file: %s . . ." % request.FILES['file'].name)
            f_name, extension = os.path.splitext(request.FILES['file'].name)
            self.handle_uploaded_file(request.FILES['file'], ambra_settings.AMBRA_INGESTION_QUEUE, "%s%s" % (article.doi, extension))
            return HttpResponseRedirect(reverse('detail_main', args=(article.doi,)))

        return HttpResponse("Form error: %s Please tell your administrator, Jack LaBarba <jlabarba@plos.org>" % form.errors)

class CorrectionsControl(View):
    template_name = 'articleflow/corrections_control.html'

    def get_context_data(self, *args, **kwargs):
        article = get_object_or_404(Article, doi=kwargs['doi'])
        ingestible_article_filename = os.path.join(ambra_settings.AMBRA_INGESTION_QUEUE, "%s.zip" % article.doi)
        ingested_article_filename = os.path.join(ambra_settings.AMBRA_INGESTED, "%s.zip" % article.doi)
        logger.debug("ingestible_filename: %s" % ingestible_article_filename)
        logger.debug("ingested_filename: %s" % ingested_article_filename)

        upload_action_url = reverse('corrections_file', args=(article.doi,))

        return {
            'form': FileUpload(article, None, upload_action_url),
            'article': article,
            'ingestible_exists': os.path.exists(ingestible_article_filename), 
            'ingested_exists': os.path.exists(ingested_article_filename),
            }
        
    def get(self, request, *args, **kwargs):
        context=self.get_context_data(*args, **kwargs)
        logger.debug(context)
        return render_to_response(self.template_name, context, context_instance=RequestContext(request))

    def post(self, request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponse("Not allowed.")
        if not request.user.is_authenticated():
            to_json = {
                'error': 'Need to login'
                }
            return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')

        # TODO check that article exists
        article = get_object_or_404(Article, doi=kwargs['doi'])
        ingestible_article_filename = os.path.join(ambra_settings.AMBRA_INGESTION_QUEUE, "%s.zip" % article.doi)
        if not os.path.exists(ingestible_article_filename):
            to_json = {
                'status': 'failure',
                'messages': 'No ingestible archive',
                'reload-errorset': False,
                }
            return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')

        # ingestprep
        ingestPrep = subprocess.Popen(["ingestPrep", ingestible_article_filename],
                                      cwd = ambra_settings.AMBRA_INGESTION_QUEUE,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE,)
        ingestPrep.wait()        
        ingestPrep_failure = (ingestPrep.returncode != 0)

        if ingestPrep_failure:
            msg = "Ingest Prep did not exit successfully. Please review any errors that may have appeared above and the following output ...\n\n"
            msg += "**Return Code: %s\n\n" % ingestPrep.returncode
            msg += "**Output**\n"
            msg += ingestPrep.stdout.read() + "\n"
            msg += "**Errors**\n"
            msg += ingestPrep.stderr.read() + "" 
            
            to_json = {
                'status': 'failure',
                'messages': msg,
                'reload-errorset': True,
                }
            return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')

        # if ingestPrep worked and user specified, run makePDF
        if request.POST.get('run_make_pdf') == 'true':
            makePDF = subprocess.Popen([settings.MAKEPDF_LOCATION,
                                        ingestible_article_filename],
                                      cwd = ambra_settings.AMBRA_INGESTION_QUEUE,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE,)
            makePDF.wait()    
            makePDF_failure = (makePDF.returncode != 0)

            if makePDF_failure:
                msg = "makePDF did not exit successfully. Please review any errors that may have appeared above and the following output ...\n\n"
                msg += "**Return Code: %s\n\n" % makePDF.returncode
                msg += "**Output**\n"
                msg += makePDF.stdout.read() + "\n"
                msg += "**Errors**\n"
                msg += makePDF.stderr.read() + "" 
            
                to_json = {
                    'status': 'failure',
                    'messages': msg,
                    'reload-errorset': True,
                }
                return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')

        # if ingestPrep ran successfully, ingest
        """
        ingest = subprocess.Popen(["/var/local/scripts/production/mechIngest", "-s", "%s.zip" % article.doi, "-f"],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,)
        ingest.wait()
        ingest_failure = (ingest.returncode != 0)
        if ingest_failure:
            msg = "mechIngest did not exit successfully. Please review any errors that may have appeared above and the following output ...\n\n"
            msg += "**Return Code: %s\n\n" % ingest.returncode
            msg += "**Output**\n"
            msg += ingest.stdout.read() + "\n"
            msg += "**Errors**\n"
            msg += ingest.stderr.read() + "" 
            
            to_json = {
                'status': 'failure',
                'messages': msg,
                'reload-errorset': True,
                }
            return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')

        response = ingest.stdout.read()
        if response.startswith('Ingested'):
            to_json = {
                'status': 'success',
                'messages': '',
                'reload-errorset': False,
                }
            return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')

        else:
            to_json = {
                'status': 'failure',
                'messages': 'Ambra ingestion error.  Ambra says: "%s"\n' % response,
                'reload-errorset': False,
                }
            return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')

        """
        r = rhyno.Rhyno(ambra_settings.AMBRA_STAGE_HOST)
        try:
            response = r.ingest("%s.zip" % article.doi, force_reingest=True)
        except Exception, e:
            to_json = {
                'status': 'failure',
                'messages': "Error in communicating to ambra: " + str(e),
                'reload-errorset': False,
                }
            return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')            

        if response.startswith('{'):
            to_json = {
                'status': 'success',
                'messages': '',
                'reload-errorset': False,
                }
            return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')

        else:
            to_json = {
                'status': 'failure',
                'messages': 'Ambra ingestion error.  Ambra says: "%s"\n' % response,
                'reload-errorset': False,
                }
            return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')
        
