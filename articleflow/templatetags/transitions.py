from django import template

from articleflow.models import Article

import logging
logger = logging.getLogger(__name__)

register = template.Library()

@register.inclusion_tag('articleflow/state_control.html', takes_context=True)
def render_article_state_control(context, article, user):
    transitions = article.possible_transitions(user)
    for t in transitions.all():
        logger.debug("Identified possible transition: %s" % t)
        if t.preference_weight < 25:
            setattr(t,'level', 'btn-danger')
        elif t.preference_weight < 50:
            setattr(t,'level', 'btn-warning')
        elif t.preference_weight < 75:
            setattr(t,'level', 'btn-primary')
        else:
            setattr(t,'level', 'btn-success')
        
    context.update({
            'article': article,
            'transitions': transitions.all().order_by('preference_weight').reverse()
            })
    return context

@register.filter()
def buttonclass(level):
    print "level: %s" % level
    if level < 25:
       return 'btn-danger'
    elif level < 50:
        return 'btn-warning'
    elif level < 75:
        return 'btn-primary'
    else:
        return 'btn-success'
