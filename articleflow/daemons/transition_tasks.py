import sys
import os
from datetime import datetime, timedelta, date
import logging

from django.db.models import Q
from django.contrib.auth.models import User
from articleflow.models import Article, State, ArticleState, Transition
from articleflow.daemons.ambra_query import *
import notification.models as notification

from celery.utils.log import get_task_logger
celery_logger = get_task_logger(__name__)
print "__name__: %s" % __name__
logger = logging.getLogger(__name__)

from celery.task import task

daemon_name_format = "daemon_%s"

QC_URGENT_THRESHOLD_DAYS = 3
WC_URGENT_THRESHOLD_DAYS = 1

def get_or_create_user(username):
    if not username:
        logger.debug("Given null username")
        return None
    if len(username) > 30:
        username = username[0:29]
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
    logger.info("%s: Article found in \'ingested\' state. determining next state . . ." % art.doi)
    ingested_state = State.objects.get(name='Ingested')
    ingested = (art.current_state == ingested_state)    
    if not ingested:
        logger.info("Article, %s, not 'Ingested' is '%s' instead.  Aborting transition to Ready for QC" % (art.doi, art.current_state))        
        return False
    ready_for_qc_state = State.objects.get(name='Ready for QC (CW)')
    ingested_state_index = ingested_state.progress_index
    try:
        state_history = ArticleState.objects.filter(article=art).filter(state__progress_index__gt=ingested_state_index)
        last_advanced_state = state_history.latest('created')
        if art.typesetter and art.typesetter not in last_advanced_state.state.typesetters.all():
            logger.info("%s: Typesetter has changed to %s, restarting QC track." % (art.doi, art.typesetter))
            raise ArticleState.DoesNotExist()

        # return article to last advanced state
        a_s = ArticleState(article=art,
                           state=last_advanced_state.state,
                           assignee=last_advanced_state.assignee,
                           from_transition=None,
                           from_transition_user=None,
                           )
        a_s.save()
        # send revision arrived notification
        if a_s.assignee:
            logger.debug("%s: Sending revision arrived notification ..." % art.doi)
            ctx = {'article': art}
            notication.send([a_s.assignee], "revision_arrived", ctx)
        
    except ArticleState.DoesNotExist, e:
        # move article to ready for qc state
        if art.typesetter and art.typesetter.name == 'Merops':
            logger.debug("%s: Merops article found, moving to Merops QC track" % art.doi)
            ready_for_qc_state = State.objects.get(unique_name='ready_for_qc_merops')
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
    ingested_state = State.objects.get(unique_name='ingested')
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

def assign_urgent_corrections_article(art, urgent_threshold):
    logger.info("%s: checking to see if it needs to be changed to Urgent Web corrections. Pubdate: %s'" % (art.doi, art.pubdate))
    non_urgent_wc_states = State.objects.filter(Q(unique_name='needs_web_corrections_cw')|Q(unique_name='needs_web_corrections_merops'))
    if art.current_state not in non_urgent_wc_states:
        logger.info("Article, %s, not in web corrections is '%s' instead.  Aborting transition to Urgent Web Corrections" % (art.doi, art.current_state))        
        return False

    if art.pubdate < add_workdays(date.today(), urgent_threshold):
        logger.info("Moving %s to Urgent Web Corrections" % art.doi)
        if art.typesetter and art.typesetter.name == 'Merops':
            urgent_transition = Transition.objects.get(unique_name='assign_to_urgent_web_corrections_merops')
        else: #assume CW
            urgent_transition = Transition.objects.get(unique_name='assign_to_urgent_web_corrections_cw')
        daemon_user = get_or_create_user(daemon_name_format % sys._getframe().f_code.co_name)

        art.execute_transition(urgent_transition, daemon_user)
 
        
def assign_urgent_corrections(urgent_threshold):
    non_urgent_wc = Article.objects.filter(Q(current_state__unique_name='needs_web_corrections_cw')|Q(current_state__unique_name='needs_web_corrections_merops'))

    for article in non_urgent_wc:
        assign_urgent_corrections_article(article, urgent_threshold)

def assign_published_stage_article(art, stage_c):
    logger.info("Checking article, %s, to see if it's pubbed on stage" % art.doi)
    ready_to_publish_state = State.objects.get(name='Ready to Publish')
    if art.current_state != ready_to_publish_state:
        logger.info("Article, %s, not 'Ready to publish' is '%s' instead.  Aborting transition to 'Published on stage'" % (art.doi, art.current_state))
        return False
    if stage_c.doi_published(art.doi):
        published_on_stage_state = State.objects.get(name='Published on Stage')
        logger.info("Article, %s, is published on stage. Moving to 'Published on Stage'" % art.doi)
        daemon_user = get_or_create_user(daemon_name_format % sys._getframe().f_code.co_name)
        a_s = ArticleState(article=art,
                           state=published_on_stage_state,
                           assignee=None,
                           from_transition=None,
                           from_transition_user=daemon_user,
                           )
        a_s.save()

# this variant will try to publish the article using a system call
def assign_published_stage_article_active(art, stage_c):
    logger.info("Checking article, %s, to see if it's pubbed on stage" % art.doi)
    ready_to_publish_state = State.objects.get(name='Ready to Publish')
    if art.current_state != ready_to_publish_state:
        logger.info("Article, %s, not 'Ready to publish' is '%s' instead.  Aborting transition to 'Published on stage'" % (art.doi, art.current_state))
        return False
    if stage_c.doi_published(art.doi):
        published_on_stage_state = State.objects.get(name='Published on Stage')
        logger.info("Article, %s, is published on stage. Moving to 'Published on Stage'" % art.doi)
        daemon_user = get_or_create_user(daemon_name_format % "publish_stage")
        a_s = ArticleState(article=art,
                           state=published_on_stage_state,
                           assignee=None,
                           from_transition=None,
                           from_transition_user=daemon_user,
                           )
        a_s.save()
    # not published? let's try to publish it
    else:
        os.system("publish %s" % art.doi)
    # and check again to see if it's published
    if stage_c.doi_published(art.doi):
        published_on_stage_state = State.objects.get(name='Published on Stage')
        logger.info("Article, %s, is published on stage. Moving to 'Published on Stage'" % art.doi)
        daemon_user = get_or_create_user(daemon_name_format % "publish_stage_active")
        a_s = ArticleState(article=art,
                           state=published_on_stage_state,
                           assignee=None,
                           from_transition=None,
                           from_transition_user=daemon_user,
                           )
        a_s.save()
        

def assign_published_stage(stage_c):
    ready_to_publish_state = State.objects.get(name='Ready to Publish') 
    ready_to_publish = Article.objects.filter(current_state=ready_to_publish_state)

    logger.info("Starting assign_published_stage.  Identified %s articles in 'Ingested' state." % ready_to_publish.count())
    for a in ready_to_publish:
        assign_published_stage_article(a, stage_c)

def assign_published_stage_active(stage_c):
    ready_to_publish_state = State.objects.get(name='Ready to Publish') 
    ready_to_publish = Article.objects.filter(current_state=ready_to_publish_state)

    logger.info("Starting assign_published_stage.  Identified %s articles in 'Ingested' state." % ready_to_publish.count())
    for a in ready_to_publish:
        assign_published_stage_article_active(a, stage_c)

def assign_published_stage_article(art, stage_c):
    logger.info("Checking article, %s, to see if it's pubbed on stage" % art.doi)
    ready_to_publish_state = State.objects.get(name='Ready to Publish')
    if art.current_state != ready_to_publish_state:
        logger.info("Article, %s, not 'Ready to publish' is '%s' instead.  Aborting transition to 'Published on stage'" % (art.doi, art.current_state))
        return False
    if stage_c.doi_published(art.doi):
        published_on_stage_state = State.objects.get(name='Published on Stage')
        logger.info("Article, %s, is published on stage. Moving to 'Published on Stage'" % art.doi)
        daemon_user = get_or_create_user(daemon_name_format % 'publish_stage')
        a_s = ArticleState(article=art,
                           state=published_on_stage_state,
                           assignee=None,
                           from_transition=None,
                           from_transition_user=daemon_user,
                           )
        a_s.save()               

def assign_published_stage(stage_c):
    ready_to_publish_state = State.objects.get(name='Ready to Publish') 
    ready_to_publish = Article.objects.filter(current_state=ready_to_publish_state)

    logger.info("Starting assign_published_stage.  Identified %s articles in 'Ready to Publish' state." % ready_to_publish.count())
    for a in ready_to_publish:
        assign_published_stage_article(a, stage_c)

def assign_published_live_article(art, live_c, force_any_state=False):
    logger.info("Checking article, %s, to see if it's pubbed on live" % art.doi)
    pubbed_stage_state = State.objects.get(name='Published on Stage')
    if art.current_state != pubbed_stage_state and not force_any_state:
        logger.info("Article, %s, not 'Published on Stage' is '%s' instead.  Aborting transition to 'Published Live'" % (art.doi, art.current_state))
        return False
    if live_c.doi_published(art.doi):
        pubbed_live_state = State.objects.get(name='Published Live')
        logger.info("Article, %s, is published on live. Moving to 'Published Live'" % art.doi)
        daemon_user = get_or_create_user(daemon_name_format % 'publish_live')
        a_s = ArticleState(article=art,
                           state=pubbed_live_state,
                           assignee=None,
                           from_transition=None,
                           from_transition_user=daemon_user,
                           )
        a_s.save()               

def assign_published_live(live_c):
    pubbed_stage_state = State.objects.get(name='Published on Stage') 
    pubbed_on_stage = Article.objects.filter(current_state=pubbed_stage_state)

    logger.info("Starting assign_published_live.  Identified %s articles in 'Published on Stage' state." % pubbed_on_stage.count())
    for a in pubbed_on_stage:
        assign_published_live_article(a, live_c)

def cleanup_published_live(live_c):
    pubbed_live_state = State.objects.get(name='Published Live')
    pubbed_live = Article.objects.exclude(current_state=pubbed_live_state)    
    logger.info("Starting exclude_published_live.  Identified %s articles in everything except 'Published on Stage' state." % pubbed_live.count())
    for a in pubbed_live:
        assign_published_live_article(a, live_c, force_any_state=True)

def main():
    stage_c = AmbraStageConnection()
    live_c = AmbraProdConnection()
    
    assign_ingested(stage_c)
    assign_ready_for_qc()
    assign_urgent(QC_URGENT_THRESHOLD_DAYS)
    assign_urgent_corrections(WC_URGENT_THRESHOLD_DAYS)
    assign_published_stage(stage_c)
    assign_published_live(live_c)

def one_time_pubbed_live_clean():
    live_c = AmbraProdConnection()
    cleanup_published_live(live_c)

def migration_sync():
    stage_c = AmbraStageConnection()
    live_c = AmbraProdConnection()
    
    assign_ingested(stage_c)
    assign_ready_for_qc()
    assign_urgent(3)
    assign_published_stage(stage_c)
    assign_published_live(live_c)
    cleanup_published_live(live_c)

@task
def ongoing_ambra_sync():
    stage_c = AmbraStageConnection()
    live_c = AmbraProdConnection()
    
    assign_ingested(stage_c)
    assign_ready_for_qc()
    assign_urgent(QC_URGENT_THRESHOLD_DAYS)
    assign_urgent_corrections(WC_URGENT_THRESHOLD_DAYS)
    assign_published_stage_active(stage_c)
    assign_published_live(live_c)

if __name__ == "__main__":
    main()
