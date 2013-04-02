import sys

from datetime import datetime, timedelta

from articleflow.models import Article, State, ArticleState, Transition

from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

from celery.task import task

daemon_name_fmt = "Daemon: %s"

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

def assign_ingested_doi(art, stage_conn):
    pulled_state = State.objects.get(name='Pulled')
    if art.current_state == pulled_state and stage_conn.doi_ingested(art.doi):
        daemon_user = get_or_create_user(daemon_name_format % sys._getframe().f_code.co_name)
        ingest_transition = Transition.objects.get(name="Ingest")
	art.execute_transition(ingest_transition, daemon_user)
        
    
def assign_ingested():
    '''
    Find all pulled articles, see if they're pubbed on stage, advance
    to Ingested if so
    '''
    pass

def assign_ready_for_qc():
    '''
    Find all ingested articles,
    Resume last state if exists,
    If not, put in ready for qc pool
    '''
    ingested_state = State.objects.get(name='Ingested')
    ingested_state_index = ingested_state.progress_index
    ingested = Article.objects.filter(current_state=ingested_state)
    ready_for_qc_state = State.objects.get(name='Ready for QC (CW)')
    
    for a in ingested:
        last_advanced_state = ArticleState.objects.filter(article=a).filter(state__progress_index__gt=ingested_state_index).latest('created')
        if last_advanced_state:
            #return article to last advanced state
            a_s = ArticleState(article=a,
                               state=last_advanced_state.state,
                               assignee=last_advanced_state.assignee,
                               from_transition=None,
                               from_transition_user=None,
                               )
            a_s.save()
        else:
            #move article to non-urgent qc
            a_s = ArticleState(article=a,
                               state=ready_for_qc_state,
                               assignee=None,
                               from_transition=None,
                               from_transition_user=None,
                               )
            a_s.save()

def assign_urgent():
    logger.info("Am I doing anything?")
    urgent_threshold = 3
    non_urgent_qc_state = State.objects.get(name='Ready for QC (CW)')
    print(non_urgent_qc_state)
    non_urgent_qc = Article.objects.filter(current_state=non_urgent_qc_state)
    print(len(non_urgent_qc))

    for article in non_urgent_qc:
        if article.pubdate < add_workdays(datetime.today, urgent_threshold):
            logger.info("Moving %s to Urgent QC (CW)" % article.doi)

def verify_published(ambra_c):
    '''
    a_connection is cursor to an ambra database
    '''
    ready_to_publish_state = State.objects.get(name='Ready to Publish')
    ready_to_publish = Articles.objects.filter(current_state=ready_to_publish_state)
    published_on_stage_state = State.objects.get(name='Published on Stage')
    
    for a in ready_to_publish:
        if is_published(a.doi, ambra_c):
            a_s = ArticleState(article=a,
                               state=published_on_stage_state,
                               assignee=None,
                               from_transition=None,
                               from_transition_user=None,
                               )
            a_s.save()            

def main():
    assign_urgent()

if __name__ == "__main__":
    main()
