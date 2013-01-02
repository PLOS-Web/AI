from django.http import HttpResponse, Http404
from django.views.generic import ListView
from django.template import Template, RequestContext
from django.shortcuts import render_to_response
import simplejson

from django.contrib.comments.models import Comment
from django.contrib.contenttypes.models import ContentType

from django.conf import settings

from errors.models import ErrorSet, Error, ErrorStatus
from articleflow.models import Article

from errors.models import STATUS_CODES

class Errors(ListView):
    template_name = 'errors/error_list.html'

    def get_queryset(self):
        return ErrorSet.objects.filter(article__doi=self.kwargs['doi']).select_related('Errors')
    
    def get_context_data(self, **kwargs):
        article = Article.objects.get(doi=self.kwargs['doi'])
        context = ({
                'article': article,
                'errorset_list': self.get_queryset()
            })
        print context
        return context

def comment_list(request, id):
    """
    Wrapper exposing comment's render_comment_list tag as a view.
    """
    # get object
    content_type = 'Errors-error'
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

def comment_block(request, pk):
    error = Error.objects.get(pk=pk)
    
    context = RequestContext(request)
    context.update({'issue': error})
    
    comments_block = render_to_response('issues/comment_block_wrapper.html', context)

    comment_count = Comment.objects.filter(
        content_type = ContentType.objects.get_for_model(Error),
        object_pk = pk,
        site__pk = settings.SITE_ID
        ).count()

    to_json = {
        'comments': comments_block.content,
        'comment_count': comment_count}

    return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')

def toggle_error_status(request):
    if request.method != "POST" or not request.is_ajax():
        raise Http404
    if not request.user.is_authenticated():
        return HttpResponse("You need to log in dummy")

    error = Error.objects.get(pk=request.POST['issue_pk'])
    requested_status = int(request.POST['status'])
    
    print requested_status

    if requested_status in map((lambda x: x[0]), STATUS_CODES):
        print "in status codes"
        i = ErrorStatus(state=requested_status,error=error)
        print "entering ErrorStatus save"
        i.save()
        print "exited ErrorStatus save"

    print error.current_status.pk

    # render error status control
    t = Template("{% load error_tags %} {% render_error_status_control error %}")
    context = RequestContext(request)
    context.update({'error': error})
    control_buttons = t.render(context)
    print control_buttons

    to_json = {'status': error.current_status.state,
               'issue-status-control': control_buttons}
    return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')

def get_error_comment_count(request, pk):
    comments = Comment.objects.filter(
        content_type = ContentType.objects.get_for_model(Error),
        object_pk = pk,
        site__pk = settings.SITE_ID
        ).count()
    to_json = {'count': comments}

    return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')
