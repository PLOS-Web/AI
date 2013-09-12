import sys
import subprocess

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from ai import settings
from ai import ambra_settings
from articleflow.models import Article, ArticleState, State, Transition

import logging
logger = logging.getLogger("commands")

from datetime import datetime
import pytz
PAC = pytz.timezone('US/Pacific')
def toUTCc(d):
    if not d:
        return None

    logger.debug("Ensuring datetime is UTC: %s" % d)
    if d.tzinfo == pytz.utc:
        logger.debug("Datetime already UTC")
        return d
    else:
        d_utc = PAC.normalize(PAC.localize(d)).astimezone(pytz.utc)
        logger.debug("Datetime converted to: %s" % d_utc)
        return d_utc

def get_web_corrections_articles(start_datetime, end_datetime=None):
    out_of_corrections_transitions = Transition.objects.filter(from_state__unique_name__icontains='correction').filter(from_state__unique_name__icontains='web')
    print out_of_corrections_transitions
    arts = ArticleState.objects.filter(from_transition__in=out_of_corrections_transitions).filter(created__gte=start_datetime)
    if end_datetime:
        pull_arts = pull_arts.filter(created__lte=end_datetime)

    # this is bad
    articles = []
    for arts in arts.all():
       if arts.article not in articles and arts.article.typesetter.name == 'CW': 
           articles += [arts.article]
    
    return sorted(articles, key=lambda a: a.pubdate)
    
def main(*args):
    start = toUTCc(datetime.strptime(args[0], "%Y-%m-%d %H:%M:%S"))
    end = None
    if len(args) > 1:
        end = toUTCc(datetime.strptime(args[1], "%Y-%m-%d %H:%M:%S"))

    articles = get_web_corrections_articles(start, end)
    print "doi, pubdate, ambra link"
    for a in articles:
        print "%s, %s, http://plosone-stage.plos.org/article/info%%3Adoi%%2F10.1371%%2Fjournal.%s" % (a.doi, a.pubdate, a.doi)

class Command(BaseCommand):
    def handle(self, *args, **options):
        main(*args)
    

