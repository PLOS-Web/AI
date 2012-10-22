from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.template import Template, RequestContext
from django.shortcuts import render_to_response
from articleflow.models import Article

def note_list(request, id):
    """
    Wrapper exposing comment's render_comment_list tag as a view.
    """
    # get object
    content_type = 'Articleflow-article'
    print "Am i working?\n"
    app_label, model = content_type.split('-')
    ctype = ContentType.objects.get(app_label=app_label, model=model)
    obj = ctype.get_object_for_this_type(id=id)

    # setup template and return result
    t = Template("{% load comments %}{% render_comment_list for object %}")
    context = RequestContext(request)
    context.update({'object': obj})
    result = t.render(context)
    return HttpResponse(result)

def note_block(request, pk):
    article = Article.objects.get(pk=pk)
    
    context = RequestContext(request)
    context.update({'article': article})
    
    return render_to_response('notes/article_note_block_wrapper.html', context)
