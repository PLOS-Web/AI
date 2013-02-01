from django import template
from django.http import QueryDict

register = template.Library()

@register.filter()
def sanitize_class_name(raw_name):
    #kinda ghetto, but didn't want to import a new lib just for this
    # ascii codes for the characters that are common and legal in html
    # class names. NOT the full legal set.
    allowed_chars = [45] + range(48,58) + range(65,91) + range(97,122)
    sanitized = ""
    for char in raw_name:
        if ord(char) in allowed_chars: sanitized += char
    return sanitized

@register.inclusion_tag('articleflow/grid_order_arrows.html', takes_context=True)
def render_ordering_arrows(context, column, base_qs, active=False):
    qs = QueryDict(base_qs).copy()
    qs['sort'] = column
    qs_asc = qs.copy()
    qs_asc['sort_type'] = 'asc'
    qs_desc = qs.copy()
    qs_desc['sort_type'] = 'desc'

    context.update({'column': column,
                    'active': active,
                    'qs_asc': qs_asc.urlencode(),
                    'qs_desc': qs_desc.urlencode()})
    return context
