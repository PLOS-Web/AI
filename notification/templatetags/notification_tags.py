from django import template

register = template.Library()

@register.inclusion_tag('notification/notification_badge.html', takes_context=True)
def notification_badge(context):
    return context
