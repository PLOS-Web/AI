from django import template

register = template.Library()

@register.filter()
def issue_count_pill(issue_count):
    if issue_count['name'] == 'XML':
        pass
        
