from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, Http404
from django.template import Template, RequestContext
from django.shortcuts import render_to_response
import simplejson

from django.db.models import Count

from django.contrib.comments.models import Comment
from django.contrib.contenttypes.models import ContentType

from django.conf import settings
from issues.models import Issue, IssueStatus, STATUS_CODES
from issues.forms import IssueForm


def comment_list(request, id):
    """
    Wrapper exposing comment's render_comment_list tag as a view.
    """
    # get object
    content_type = 'Issues-issue'
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
    issue = Issue.objects.get(pk=pk)
    
    context = RequestContext(request)
    context.update({'issue': issue})
    
    comments_block = render_to_response('issues/comment_block_wrapper.html', context)

    comment_count = Comment.objects.filter(
        content_type = ContentType.objects.get_for_model(Issue),
        object_pk = pk,
        site__pk = settings.SITE_ID
        ).count()

    to_json = {
        'comments': comments_block.content,
        'comment_count': comment_count}

    return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')
    

def issue_block(request, pk):
    issue = Issue.objects.get(pk=pk)
    context = RequestContext(request)

    context.update({'issue': issue})

    return render_to_response('issues/issue_block.html', context)

def post_issue(request):
    if request.method == "POST":
        if not request.user.is_authenticated():
            return HttpResponse("You need to log in dummy")
        form = IssueForm(data=request.POST)
        if request.is_ajax():
            # ajax and valid
            if form.is_valid():
                issue = form.save()
                issue_html = issue_block(request, issue.pk)
                form = IssueForm(initial={'article': request.POST['article'], 'submitter': request.user})
                print form
                form_html = render_to_response(
                    'issues/issue_form.html',
                    {
                        "form": form
                        },
                    context_instance=RequestContext(request)
                    )
                print form_html.content
                to_json = {
                    'issue_html': issue_html.content,
                    'form_html': form_html.content,
                    }
                return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')
            # ajax and not valid
            else:
                form_html = render_to_response(
                    'issues/issue_form.html',
                    {
                        "form": form
                        },
                    context_instance=RequestContext(request)
                    )
                to_json = {
                    'error': 'Invalid submission',
                    'form_html': form_html.content,
                    }
                return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')
        else:
            # not ajax but valid
            if form.is_valid():
                form.save()
                return HttpResponse("Thank you for your comment, but you'll have a lot more fun if javascript was working.")
            # not ajax and not valid
            else:
                return render_to_response(
                    'issues/issue_form.html',
                    {
                        "form": form
                        },
                    context_instance=RequestContext(request)
                    )
    else:
        form = IssueForm()
    return render_to_response(
        'issues/issue_form.html',
        {
            "form": form
            },
        context_instance=RequestContext(request)
        )

def toggle_issue_status(request):
    if request.method != "POST" or not request.is_ajax():
        raise Http404
    if not request.user.is_authenticated():
        return HttpResponse("You need to log in dummy")

    issue = Issue.objects.get(pk=request.POST['issue_pk'])
    requested_status = int(request.POST['status'])
    
    print requested_status

    if requested_status in map((lambda x: x[0]), STATUS_CODES):
        print "in status codes"
        i = IssueStatus(status=requested_status,issue=issue)
        print "entering IssueStatus save"
        i.save()
        print "exited IssueStatus save"

    print issue.current_status.pk

    # render issue status control
    t = Template("{% load ajax_issues %} {% render_issue_status_control issue %}")
    context = RequestContext(request)
    context.update({'issue': issue})
    control_buttons = t.render(context)

    to_json = {'status': issue.current_status.status,
               'issue-status-control': control_buttons}
    return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')
    
def get_issue_comment_count(request, pk):
    #if request.method != "POST" or not request.is_ajax():
    #    raise Http404

    comments = Comment.objects.filter(
        content_type = ContentType.objects.get_for_model(Issue),
        object_pk = pk,
        site__pk = settings.SITE_ID
        ).count()
    to_json = {'count': comments}

    return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')
