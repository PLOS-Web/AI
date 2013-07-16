from django import template

from django.contrib.auth.models import User, Group

import logging
logger = logging.getLogger(__name__)

register = template.Library()

@register.filter()
def is_manager(user):
    return (user.groups.filter(name='management'))
