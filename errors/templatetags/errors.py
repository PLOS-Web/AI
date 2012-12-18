from django import template

register = template.Library()

@register.inclusion_tag('errors/errorset.html', takes_context=True)
def render_errorset_block(context, errorset):
    context.update({'errorset': errorset})
    return context

@register.inclusion_tag('errors/error_block.html', takes_context=True)
def render_error_block(context, error):
    context.update({'error': error})
    return context
    
    
