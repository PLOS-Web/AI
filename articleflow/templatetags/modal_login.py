from django import template

register = template.Library()

@register.inclusion_tag('login_modal_trigger.html')
def render_login_trigger(user):
    return {'user': user}

@register.inclusion_tag('login_modal.html')
def render_login_modal():
    return {}
