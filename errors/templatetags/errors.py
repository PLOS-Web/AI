from django import template

register = template.Library()

@register.inclusion_tag('errors/errorset.html', takes_context=True)
def render_errorset_block(context, errorset):
    context.update({'errorset': errorset})
    return context
