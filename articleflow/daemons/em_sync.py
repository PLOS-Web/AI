import re
from datetime import datetime
import pytz

from celery.task import task

import em_query
from em_query import EMQueryConnection
from articleflow.models import Article, State, ExternalSync, SyncHistory

EAST_TZ = pytz.timezone('US/Eastern')

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

def get_live_articles():
    # will throw State.DoesNotExist error if no 'Published Live' state
    cutoff_state_index = State.objects.get(name='Published Live').progress_index
    return Article.objects.filter(current_state__progress_index__lt=cutoff_state_index).order_by('journal')
    
def sync_live_pubdates():
    articles = get_live_articles()
    logger.info("Found %s pre-publication articles.  Updating pubdates . . ." % articles.count())
    articles = articles[:5]

    with EMQueryConnection() as eqc:
        for a in articles:
            logger.info("Pulling new pubdate for %s" % a.doi)
            try:
                s_time = datetime.now()
                pubdate = eqc.get_pubdate(a.doi)
                logger.info("Completed query in %s seconds" % (datetime.now() - s_time))
                #a.pubdate = pubdate
                #a.save()
            except LookupError, e:
                logger.error(e)
            except ValueError, e:
                logger.error(e)
@task
def sync_all_pubdates():
    with EMQueryConnection() as eqc:
        pubdates = eqc.get_all_pubdates()
        short_doi_prog = re.compile('(?<=10\.1371\/journal\.).*')
        for a in pubdates:
            # only update AI's pubdate if EM has a non-null value
            if a[1]:
                try:
                    short_doi = short_doi_prog.search(a[0]).group(0)
                    article = Article.objects.get(doi=short_doi)
                    article.pubdate = a[1]
                    article.em_pk = a[2]
                    article.em_ms_number = a[3]
                    article.em_max_revision = a[4]
                    logger.info("Updating %s with pubdate, %s" % (article, a[1]))
                    article.save()
                except Article.DoesNotExist, e:
                    logger.error("Pubdate update couldn't find doi, %s, in AI" % short_doi)
            else:
                logger.error("EM provided a null pubdate for %s. Not updating." % a[0])

@task
def sync_most_recent_em_changes():
    with EMQueryConnection() as eqc:
        extsync, new = ExternalSync.objects.get_or_create(name=__name__)
        if new: extsync.save()

        last_sync = extsync.latest_sync
        print(vars(last_sync))
        if last_sync:
            mtime = last_sync.max_external_timestamp
            logger.info("Using last mtime: %s" % mtime)
        else: mtime = None
        
        job = extsync.start_sync()
        pubdates = eqc.sync_all_after_mtime(mtime)
        short_doi_prog = re.compile('(?<=10\.1371\/journal\.).*')
        for a in pubdates:
            # only update AI's pubdate if EM has a non-null value
            if a[1]:
                try:
                    short_doi = short_doi_prog.search(a[0]).group(0)
                    article = Article.objects.get(doi=short_doi)
                    article.pubdate = a[1]
                    article.em_pk = a[2]
                    article.em_ms_number = a[3]
                    article.em_max_revision = a[4]
                    logger.info("Updating %s with pubdate, %s" % (article, a[1]))
                    article.save()
                except Article.DoesNotExist, e:
                    logger.error("Pubdate update couldn't find doi, %s, in AI" % short_doi)
            else:
                logger.error("EM provided a null pubdate for %s. Not updating." % a[0])
        max_mtime = max(map(lambda x: x[5], pubdates))
        job.max_external_timestamp = EAST_TZ.localize(max_mtime)
        job.save()
        job.complete()


@task
def cron_test():
    for i in range(0,11):
        logger.info("Cron test activated %s" % i)
    return True
    
def main():
    sync_most_recent_em_changes()

if __name__ == "__main__":
    main()
