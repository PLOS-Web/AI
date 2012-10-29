from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse
from django.template import Template, RequestContext
from django.shortcuts import render_to_response
from issues.models import Issue
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
            if form.is_valid():
                issue = form.save()
                return issue_block(request, issue.pk)
        else:
            if form.is_valid():
                form.save()
                return HttpResponse("Thank you for your comment, but please turn on javascript.")
    else:
        form = IssueForm()
    return render_to_response(
        'issues/issue_form.html',
        {
            "form": form
            },
        context_instance=RequestContext(request)
        )
            
    

        
