from django import template
from articleflow.models import State
from django.contrib.auth.models import User, Group

register = template.Library()

@register.inclusion_tag('articleflow/assign_to_me_button.html', takes_context=True)
def render_assign_to_me_button(context, article, user):
    a_state = article.current_state
    if a_state.worker_groups.filter(user=user):
        context.update({'legal_to_assign': True})
    else:
        context.update({'legal_to_assign': False})

    return context
    
    
