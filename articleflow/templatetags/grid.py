from django import template
from django.http import QueryDict
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse

register = template.Library()

@register.filter()
def sanitize_class_name(raw_name):
    #kinda ghetto, but didn't want to import a new lib just for this
    # ascii codes for the characters that are common and legal in html
    # class names. NOT the full legal set.
    allowed_chars = [45] + range(48,58) + range(65,91) + range(97,122)
    sanitized = ""
    for char in raw_name:
        if ord(char) in allowed_chars: sanitized += char
    return sanitized

@register.inclusion_tag('articleflow/grid_order_arrows.html', takes_context=True)
def render_ordering_arrows(context, column, base_qs):
    qs = QueryDict(base_qs).copy()
    active = False

    if qs.get('order_col') == column:
        if qs.get('order_mode') == 'asc':
            active = 'asc'
        else:
            active = 'desc'

    print active
    qs['order_col'] = column
    qs_asc = qs.copy()
    qs_asc['order_mode'] = 'asc'
    qs_desc = qs.copy()
    qs_desc['order_mode'] = 'desc'

    context.update({'column': column,
                    'active': active,
                    'qs_asc': qs_asc.urlencode(),
                    'qs_desc': qs_desc.urlencode()})
    return context

@register.simple_tag()
def preconfigured_grid(user):
    user_groups = user.groups.all()
    prod_group = Group.objects.get(name='production')
    web_group = Group.objects.get(name='web')
    if (prod_group in user_groups or web_group in user_groups):
        return reverse('grid') + ('?doi=&pubdate_gte=&pubdate_lte=&current_assignee=%s&page_size=100&submit=Search' % user.pk)

    zyg_group = Group.objects.get(name='zyg')
    if zyg_group in user_groups:
        return reverse('grid') + '?doi=&pubdate_gte=&pubdate_lte=&journal=1&current_articlestate=63&current_articlestate=86&state_started_gte=&state_stated_lte=&page_size=50&submit=Search'

    return reverse('grid')
    
@register.inclusion_tag('articleflow/grid_search.html', takes_context=True)
def render_grid_search(context, expanded=False):
    context['expanded'] = expanded
    return context
