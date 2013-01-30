from django import template

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
