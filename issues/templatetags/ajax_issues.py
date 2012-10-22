from django import template

from issues.models import Issue

register = template.Library()

@register.inclusion_tag('issues/issue_block.html', takes_context=True)
def render_issue_block(context, article, user):
    issues = Issue.objects.filter(article=article)
    context.update({'issues': issues,
                    'user': user})
    return context
