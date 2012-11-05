from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, Http404
from django.template import Template, RequestContext
from django.shortcuts import render_to_response
from issues.models import Issue
from issues.forms import IssueForm
import simplejson

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
    
    return render_to_response('issues/comment_block_wrapper.html', context)

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
    print ("Was issue %s, but want to change to %s. " % (issue.status, request.POST['status']))
    requested_status = int(request.POST['status'])

    if requested_status == 0:
        print ("Changing to 0. ")
        issue.status = 0
        issue.save()
    elif requested_status == 1:
        print ("Changing to 1. ")
        issue.status = 1
        issue.save()

    print ("Now issue %s\n" % issue.status)    
    to_json = {'status': issue.status}
    return HttpResponse(simplejson.dumps(to_json), mimetype='application/json')
    
