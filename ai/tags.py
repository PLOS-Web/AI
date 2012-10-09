from django import template

register = template.library()

@register.tag
def active(request, pattern):
    import re
    print request
    if re.search(pattern, request.path):
        return 'active'
    return ''
