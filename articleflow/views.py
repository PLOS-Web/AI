from django.http import HttpResponse
from django.shortcuts import render_to_response
from articleflow.models import Article, ArticleState, State

def grid(request):
    articles = Article.objects.all().order_by('created')
    ctx = {'articles': articles}
    return render_to_response('articleflow/grid.html', ctx)

def detail(request, doi=None):
    article = Article.objects.get(doi=doi)
    ctx = {'article': article}
    return render_to_response('articleflow/detail.html',ctx)
