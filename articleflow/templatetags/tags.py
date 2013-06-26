from django import template
import pprint

register = template.Library()

@register.tag
def active(parser, pattern):
    import re
    if re.search(pattern, parser.path):
        return 'active'
    return ''
