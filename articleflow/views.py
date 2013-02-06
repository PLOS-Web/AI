from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.generic import ListView, DetailView
from django.views.generic.base import View
from django.template import RequestContext
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django import forms
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import Group

import simplejson

import django_filters

import transitionrules

from articleflow.models import Article, ArticleState, State, Transition, Journal
from issues.models import Issue, Category
from errors.models import ErrorSet, Error, ERROR_LEVEL

COLUMN_CHOICES = (
    (0, 'DOI'),
    (1, 'PubDate'),
    (2, 'Journal'),
    (3, 'Issues'),
    (4, 'Errors'),
    (5, 'State'),
    (6, 'Assigned'),
    )

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

    @staticmethod
    def assigned(a, type):
        return a.order_by(ColumnOrder.parse_type(type) + 'current_articlestate__assignee__username')
    
ORDER_CHOICES = {
    'DOI': ColumnOrder.doi,
    'PubDate' : ColumnOrder.pubdate,
    'Journal' : ColumnOrder.journal,
    'Issues' : ColumnOrder.issues,
    'Errors' : ColumnOrder.errors,
    'State' : ColumnOrder.state,
    'Assigned' : ColumnOrder.assigned,
}


class ArticleFilter(django_filters.FilterSet):
    
    doi = django_filters.CharFilter(name='doi', label='DOI')


    datepicker_widget = forms.DateInput(attrs={'class': 'datepicker'})
    pubdate_gte = django_filters.DateFilter(name='pubdate', label='Pubdate on or after', lookup_type='gte', widget=datepicker_widget) 
    pubdate_lte = django_filters.DateFilter(name='pubdate', label='Pubdate on or before', lookup_type='lte', widget=datepicker_widget) 

    journal = django_filters.ModelMultipleChoiceFilter(name='journal', label='Journal', queryset=Journal.objects.all())
    current_articlestate = django_filters.ModelMultipleChoiceFilter(name='current_state', label='Article state', queryset=State.objects.all())
    current_articlestate = django_filters.ModelMultipleChoiceFilter(name='current_articlestate__assignee', label='Assigned', queryset=User.objects.all())
    
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
                    if group in transition.allowed_groups:
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
