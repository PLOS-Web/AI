from django import template
from django.template import Template, RequestContext

register = template.Library()

@register.inclusion_tag('notes/article_note_block_wrapper.html')
def render_article_note_block(article, user):
    return {'article': article,
            'user': user}
