from django import template
from articleflow.models import Article


register = template.Library()

@register.inclusion_tag('articleflow/corrections_control_wrapper.html', takes_context=True)
def render_corrections_control(context, article):
    return context
