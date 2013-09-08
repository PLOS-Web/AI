from django import template
from articleflow.models import Article
from django.contrib.auth.models import Group

register = template.Library()

@register.filter(name='is_corrector')
def is_corrector(user):
    try:
        g = Group.objects.get(name='web correctors')
    except Group.DoesNotExist, e:
        return False

    return (g in user.groups.all())

@register.filter(name='is_web_corrections_outsourcer')
def is_web_corrections_outsourcer(user):
    try:
        g = Group.objects.get(name='web corrections outsourcers')
    except Group.DoesNotExist, e:
        return False

    return (g in user.groups.all())
    

@register.inclusion_tag('articleflow/corrections_control_wrapper.html', takes_context=True)
def render_corrections_control(context, article):
    return context
