from django import template

from articleflow.models import Article

register = template.Library()

@register.inclusion_tag('articleflow/state_control.html', takes_context=True)
def render_article_state_control(context, article):
    transitions = article.possible_transitions()
    print "transitions: "
    for t in transitions.all():
        print(t)
    context.update({
            'article': article,
            'transitions': transitions.all()
            })
    return context

    
