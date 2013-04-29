from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def ordered_flat_dict(dictionary):
    return sorted(dictionary.items())
    
