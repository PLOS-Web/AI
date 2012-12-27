from django import template

from issues.models import Issue
from issues.forms import IssueForm

register = template.Library()

@register.inclusion_tag('issues/issue_block.html', takes_context=True)
def render_issue_block(context, issue):
    context.update({'issues': issue})
    return context

@register.inclusion_tag('issues/issues.html', takes_context=True)
def render_issues(context, article):
    issues = Issue.objects.filter(article=article)
    context.update({'issues': issues})
    return context

@register.inclusion_tag('issues/issue_form.html', takes_context=True)
def render_issue_form(context, article, user):
    form = IssueForm(initial={'article': article, 'submitter': user})
    context.update({'form': form})
    
    return context
    
@register.inclusion_tag('issues/issue_status_control.html', takes_context=True)
def render_issue_status_control(context, issue):
    context.update({'issue': issue})
    return context
        
