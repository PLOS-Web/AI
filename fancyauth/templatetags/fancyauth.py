from django import template

register = template.Library()

@register.inclusion_tag('fancyauth/login_modal_link.html')
def render_login_modal_link(link_text):
    return {'link_text': link_text}

@register.inclusion_tag('fancyauth/logout_link.html')
def render_logout_link(link_text):
    return {'link_text': link_text}

@register.inclusion_tag('fancyauth/login_modal_trigger.html')
def render_login_trigger(user):
    return {'user': user}

@register.inclusion_tag('fancyauth/login_modal.html')
def render_login_modal(request):
    return {'request': request}
