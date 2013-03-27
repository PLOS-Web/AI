import em_query
from em_query import EMQueryConnection
from articleflow.models import Article, State

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

def get_live_articles():
    # will throw State.DoesNotExist error if no 'Published Live' state
    cutoff_state_index = State.objects.get(name='Published Live').progress_index
    return Article.objects.filter(current_state__progress_index__lt=cutoff_state_index)
    
def sync_live_pubdates():
    articles = get_live_articles()

    with EMQueryConnection() as eqc:
        for a in articles:
            logger.info("Pulling new pubdate for %s" % a.doi)
            try:
                pubdate = eqc.get_pubdate(a.doi)
                a.pubdate = pubdate
                a.save()
            except LookupError, e:
                logger.error(e)
            except ValueError, e:
                logger.error(e)
    
def main():
    sync_live_pubdates()

if __name__ == "__main__":
    main()
