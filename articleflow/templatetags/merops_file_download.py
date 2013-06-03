from django import template

register = template.Library()

@register.inclusion_tag('articleflow/merops_file_download.html')
def render_merops_hopper_downloads(article):
    return {'article': article}
