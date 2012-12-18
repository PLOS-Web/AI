from django.http import HttpResponse, Http404
from django.views.generic import ListView
import simplejson

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


def toggle_error_status(request):
    if request.method != "POST" or not request.is_ajax():
        raise Http404
    if not request.user.is_authenticated():
        return HttpResponse("You need to log in dummy")

    error = Error.objects.get(pk=request.POST['error_pk'])
    requested_status = int(request.POST['status'])
    
    print requested_status

    if requested_status in map((lambda x: x[0]), STATUS_CODES):
        print "in status codes"
        i = ErrorStatus(state=requested_status,error=error)
        print "entering ErrorStatus save"
        i.save()
        print "exited ErrorStatus save"

    to_json = {'status': error.current_status.state}
    return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')


def get_error_comment_count(request, pk):
    comments = Comment.objects.filter(
        content_type = ContentType.objects.get_for_model(Error),
        object_pk = pk,
        site__pk = settings.SITE_ID
        ).count()
    to_json = {'count': comments}

    return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')
