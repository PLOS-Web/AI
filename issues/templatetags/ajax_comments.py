from django import template
from django.template.loader import render_to_string
from django.shortcuts import render_to_response
from django.template import Template, RequestContext
from issues.views import comment_block

from issues.models import Issue

register = template.Library()

@register.inclusion_tag('issues/comment_block_wrapper.html', takes_context=True)
def render_comment_block(context, issue):
    context.update({'issue': issue})
    return context
