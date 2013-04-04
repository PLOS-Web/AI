import sys

from datetime import datetime, timedelta, date

from django.contrib.auth.models import User
from articleflow.models import Article, State, ArticleState, Transition

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

from celery.task import task

daemon_name_format = "Daemon: %s"

def get_or_create_user(username):
    if not username:
        logger.debug("Given null username")
        return None
    try:
        u = User.objects.get(username=username)
        logger.debug("Found user: %s" % u.username)
    except User.DoesNotExist:
        logger.debug("Creating user for: %s" % username)
        u = User(username=username, password='Well this is a fun way to do things')
        u.save()
    return u

def is_ingested(doi, ambra_c):
        ambra_c.execute(
            """"
            SELECT
               a.doi
            FROM article as a
            WHERE a.state = 1
            """)
        res = ambra_c.fetchall()
        if res:
            return True
        return False

def is_published(doi, ambra_c):
        ambra_c.execute(
            """"
            SELECT
               a.doi
            FROM article as a
            WHERE a.state = 0
            """)
        res = ambra_c.fetchall()
        if res:
            return True
        return False

def add_workdays(start_date, delta_days, whichdays=(0,1,2,3,4)):
    new_date = start_date
    d = delta_days
    while d:
        new_date = new_date + timedelta(days=1)
        if new_date.weekday() in whichdays:
            d -= 1
    return new_date

def assign_ingested_article(art, stage_conn):
    logger.info("Checking article, %s, to see if it needs to be changed to 'Ingested'" % art.doi)
    pulled_state = State.objects.get(name='Pulled')
    pulled = (art.current_state == pulled_state)
    ingested = stage_conn.doi_ingested(art.doi)
    logger.info("Article %s:  {pulled: %s, ingested: %s}" % (art.doi, pulled, ingested)) 
    if pulled and ingested:
        logger.info("Article, %s, moving to 'Ingested'" % art.doi)
        daemon_user = get_or_create_user(daemon_name_format % sys._getframe().f_code.co_name)
        ingest_transition = Transition.objects.get(name="Ingest")
	art.execute_transition(ingest_transition, daemon_user)
        
    
def assign_ingested(stage_conn):
    '''
    Find all pulled articles, see if they're pubbed on stage, advance
    to Ingested if so
    '''
    pulled_state = State.objects.get(name='Pulled')
    pulled_articles = Article.objects.filter(current_state=pulled_state).all()
    for a in pulled_articles:
        assign_ingested_article(a, stage_conn)

def assign_ready_for_qc_article(art):
    logger.info("Checking article, %s, to see if it needs to be changed to 'Ready for QC (CW)'" % art.doi)
    ingested_state = State.objects.get(name='Ingested')
    ingested = (art.current_state == ingested_state)    
    if not ingested:
        logger.info("Article, %s, not 'Ingested' is '%s' instead.  Aborting transition to Ready for QC" % (art.doi, art.current_state))        
        return False
    ready_for_qc_state = State.objects.get(name='Ready for QC (CW)')
    ingested_state_index = ingested_state.progress_index
    try:
        last_advanced_state = ArticleState.objects.filter(article=art).filter(state__progress_index__gt=ingested_state_index).latest('created')
        # return article to last advanced state
        a_s = ArticleState(article=art,
                           state=last_advanced_state.state,
                           assignee=last_advanced_state.assignee,
                           from_transition=None,
                           from_transition_user=None,
                           )
        a_s.save()
    except ArticleState.DoesNotExist, e:
        # move article to ready for qc state
        a_s = ArticleState(article=art,
                           state=ready_for_qc_state,
                           assignee=None,
                           from_transition=None,
                           from_transition_user=None,
                           )
        a_s.save()

def assign_ready_for_qc():
    '''
    Find all ingested articles,
    Resume last state if exists,
    If not, put in ready for qc pool
    '''
    ingested_state = State.objects.get(name='Ingested')
    ingested = Article.objects.filter(current_state=ingested_state)
    logger.info("Starting assign_ready_for_qc.  Identified %s articles in 'Ingested' state." % ingested.count())
    
    for a in ingested:
        assign_ready_for_qc_article(a)

def assign_urgent_article(art, urgent_threshold):
    logger.info("Checking article, %s, to see if it needs to be changed to 'Urgent QC (CW). Pubdate: %s'" % (art.doi, art.pubdate))
    non_urgent_qc_state = State.objects.get(name='Ready for QC (CW)')
    if art.current_state != non_urgent_qc_state:
        logger.info("Article, %s, not 'Ready for QC (CW)' is '%s' instead.  Aborting transition to Urgent QC" % (art.doi, art.current_state))        
        return False

    urgent_qc_state = State.objects.get(name='Urgent QC (CW)')
    if art.pubdate < add_workdays(date.today(), urgent_threshold):
        logger.info("Moving %s to Urgent QC (CW)" % art.doi)
        daemon_user = get_or_create_user(daemon_name_format % sys._getframe().f_code.co_name)
        a_s = ArticleState(article=art,
                           state=urgent_qc_state,
                           assignee=None,
                           from_transition=None,
                           from_transition_user=daemon_user,
                           )
        a_s.save()        
        
def assign_urgent(urgent_threshold):
    non_urgent_qc_state = State.objects.get(name='Ready for QC (CW)') 
    non_urgent_qc = Article.objects.filter(current_state=non_urgent_qc_state)

    for article in non_urgent_qc:
        assign_urgent_article(article, urgent_threshold)

def verify_published(ambra_c):
    '''
    a_connection is cursor to an ambra database
    '''
    ready_to_publish_state = State.objects.get(name='Ready to Publish')
    ready_to_publish = Articles.objects.filter(current_state=ready_to_publish_state)
    published_on_stage_state = State.objects.get(name='Published on Stage')
    
    for a in ready_to_publish:
        if is_published(a.doi, ambra_c):
            daemon_user = get_or_create_user(daemon_name_format % sys._getframe().f_code.co_name)
            a_s = ArticleState(article=a,
                               state=published_on_stage_state,
                               assignee=None,
                               from_transition=None,
                               from_transition_user=daemon_user,
                               )
            a_s.save()            

def main():
    assign_urgent()

if __name__ == "__main__":
    main()
