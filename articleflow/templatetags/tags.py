from django import template
import pprint

register = template.Library()

@register.tag
def active(parser, pattern):
    import re
    pprint.pprint(parser)
    print parser.next_token()
    if re.search(pattern, parser.path):
        return 'active'
    return ''
