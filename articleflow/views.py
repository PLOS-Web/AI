from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.generic import ListView, DetailView
from django.views.generic.base import View
from django.template import RequestContext
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django import forms
import simplejson

import django_filters

import transitionrules

from articleflow.models import Article, ArticleState, State, Transition, Journal
from issues.models import Issue, Category

class ColumnHandler():
    @staticmethod
    def doi(a):
        return a.doi

    @staticmethod
    def pubdate(a):
        return a.pubdate

    @staticmethod
    def journal_name(a):
        return a.journal.short_name

    @staticmethod
    def state(a):
        return a.current_articlestate.state.name
        

COLUMN_CHOICES = (
    (0, 'DOI', ColumnHandler.doi),
    (1, 'PubDate', ColumnHandler.pubdate),
    (2, 'Journal', ColumnHandler.journal_name),
    (3, 'Issues', 'lala'),
    (4, 'Notes', 'lala'),
    (5, 'State', ColumnHandler.state),
    )

class ArticleFilter(django_filters.FilterSet):
    doi = django_filters.CharFilter(name='doi', label='DOI')

    datepicker_widget = forms.DateInput(attrs={'class': 'datepicker'})
    pubdate_gte = django_filters.DateFilter(name='pubdate', label='Pubdate on or after', lookup_type='gte', widget=datepicker_widget) 
    pubdate_lte = django_filters.DateFilter(name='pubdate', label='Pubdate on or before', lookup_type='lte', widget=datepicker_widget) 

    journal = django_filters.ModelMultipleChoiceFilter(name='journal', label='Journal', queryset=Journal.objects.all())
    current_articlestate = django_filters.ModelMultipleChoiceFilter(name='current_articlestate__state', label='Article state', queryset=State.objects.all())
    
    class Meta:
        model = Article
        fields = []

class ArticleGrid(View):    
    template_name = 'articleflow/grid.html'

    def get_selected_cols(self):
        if not self.request.GET.getlist('cols'):
            requested_cols = range(0,2)
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
        #context['article_list'] = Article.objects.all().select_related('journal__name', 'articlestate__state__name')
        
        raw_list = ArticleFilter(self.request.GET, queryset=Article.objects.all())
        print raw_list

        requested_cols = self.get_selected_cols()

        annotated_list = [] 
        
        for article in raw_list:
            a_annotated = []
            for col in requested_cols:
                fn = COLUMN_CHOICES[int(col)][2]
                a_annotated.append((COLUMN_CHOICES[int(col)][1], fn(article)))
            annotated_list.append(a_annotated)
            print a_annotated

        context['article_list'] = annotated_list
        context['filter_form'] = raw_list.form
        context['requested_cols'] = self.get_selected_cols_names(requested_cols)

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

