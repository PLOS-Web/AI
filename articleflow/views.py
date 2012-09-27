from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from articleflow.models import Article, ArticleState, State
from django.views.generic import ListView, DetailView

class ArticleGrid(ListView):

    template_name = 'articleflow/grid.html'

    def get_queryset(self):
        articles = Article.objects.all().select_related()
        for art in articles:
            art['current_articlestate'] = art.current_articlestate()
        return articles

class ArticleDetail(DetailView):

    slug_field = 'doi'
    template_name = 'articleflow/detail.html'

    def get_queryset(self):
        return Article.objects.all()


