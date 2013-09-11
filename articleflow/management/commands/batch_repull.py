import sys
import subprocess

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from ai import settings
from ai import ambra_settings
from articleflow.models import Article, ArticleState, State

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

def get_deliveries(start_datetime, end_datetime=None):
    pull_arts = ArticleState.objects.filter(Q(state__unique_name='delivered')|Q(state__unique_name='ready_to_build_article_package')).filter(created__gte=start_datetime)
    if end_datetime:
        pull_arts = pull_arts.filter(created__lte=end_datetime)

    # this is bad
    articles = []
    for arts in pull_arts.all():
       if arts.article not in articles:
           if arts.state == State.objects.get(unique_name='delivered'):
               articles += [(arts.article, 'ariesPull')]
           if arts.state == State.objects.get(unique_name='ready_to_build_article_package'):
               articles += [(arts.article, '/var/local/scripts/production/ariesPullMerops')]

    print articles
    return articles
    
def main(*args):
    start = toUTCc(datetime.strptime(args[0], "%Y-%m-%d %H:%M:%S"))
    end = None
    if len(args) > 1:
        end = toUTCc(datetime.strptime(args[1], "%Y-%m-%d %H:%M:%S"))

    articles = get_deliveries(start, end)
    for a in articles:
        logger.info("Repulling %s . . ." % a[0].doi)
        p = subprocess.Popen([a[1], a[0].doi], cwd=ambra_settings.AMBRA_INGESTION_QUEUE)
        p.wait()
        logger.info("return: %s " % p.returncode)

class Command(BaseCommand):
    def handle(self, *args, **options):
        main(*args)
    

