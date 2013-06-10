from django import template
from articleflow.models import State
from django.contrib.auth.models import User, Group

from articleflow.forms import AssignArticleForm
from articleflow.models import Article

register = template.Library()

@register.inclusion_tag('articleflow/assign_to_me_button.html', takes_context=True)
def render_assign_to_me_button(context, article, user):
    a_state = article.current_state
    if a_state.worker_groups.filter(user=user):
        context.update({'legal_to_assign': True})
    else:
        context.update({'legal_to_assign': False})

    return context

@register.inclusion_tag('articleflow/assign_article_form.html', takes_context=True)
def render_assign_article_form(context, article):
    form = AssignArticleForm(article)
    ctx = {
        'form': form
            }
    return ctx
    
@register.filter()
def joinby(value, arg):
    return arg.join(value)  
