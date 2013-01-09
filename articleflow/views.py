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
    
    def get_context_data(self, **kwargs):
        #context = super(ArticleGrid, self).get_context_data(**kwargs)
        
        context = {}
        context['article_list'] = Article.objects.all().select_related('journal__name', 'articlestate__state__name')
        context['article_list'] = ArticleFilter(self.request.GET, queryset=Article.objects.all())
        return context
    #def get(self, request, *args, **kwargs):

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
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
            article = Article.objects.get(pk=request.POST['article'])
            transition = Transition.objects.get(pk=request.POST['transition'])
            # @TODO, fix this shit!
            user = User.objects.get(pk=1)

            open_items = article_count_open_items(article)
            if (items.open_issues > 0 or items.open_errors > 0):
                to_json = {
                    'open_item_error': {
                        'open_isses': open_items.open_issues,
                        'open_errors': open_items.open_errors
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

