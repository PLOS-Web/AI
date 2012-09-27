from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from articleflow.models import Article, ArticleState, State
from django.views.generic import ListView, DetailView

class ArticleGrid(ListView):

    template_name = 'articleflow/grid.html'

    def get_queryset(self):
        return Article.objects.all().select_related('journal__name', 'articlestate__state__name')

class ArticleDetail(DetailView):

    slug_field = 'doi'
    template_name = 'articleflow/detail.html'

    def get_queryset(self):
        return Article.objects.all()


