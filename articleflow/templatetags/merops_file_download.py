from django import template
from articleflow.models import State

register = template.Library()

@register.inclusion_tag('articleflow/merops_file_download.html')
def render_merops_hopper_downloads(article):
    meropsed = article.article_states.filter(state__unique_name = 'meropsed')
    finish_xml_complete = article.article_states.filter(state__unique_name = 'finish_out')
    
    return {
        'meropsed': bool(meropsed),
        'finish_xml_complete': bool(finish_xml_complete),
        'article': article,
        }
