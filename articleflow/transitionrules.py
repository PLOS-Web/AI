from articleflow.models import Article
from issues.models import Issue, IssueStatus
from errors.models import Error, ErrorStatus, ErrorSet

import logging
logger = logging.getLogger(__name__)

# ghetto polymorphic function
def ready_to_ignore(item):
    if isinstance(item, Issue):
        if item.current_status.status in (2, 3):
            return True
        return False
    if isinstance(item, Error):
        if item.current_status.state in (2,3):
            return True
        if (item.current_status.state == 1 and item.level == 2):
            return True
        return True

def article_count_open_items(article):
    open_errors = 0
    open_issues = 0

    for i in article.issues.all():
        if not ready_to_ignore(i):
            open_issues += 1
    logger.info("Found %s open issues for %s" % (open_issues, article.doi))

    try:
        latest_errorset = article.error_sets.latest('created')
        for e in latest_errorset.errors.all():
            if not ready_to_ignore(i):
                open_errors += 1
        logger.info("Found %s open errors for %s" % (open_errors, article.doi))
    except ErrorSet.DoesNotExist, e:
        logger.info("No ErrorSets found for %s : open_errors=0" % article.doi)
        open_errors = 0

    return {
        'open_issues': open_issues,
        'open_errors': open_errors,
        }

def article_no_open_items(article):
    items = article_count_open_items(article)
    if (items.open_issues == 0 and items.open_errors == 0):
        logger.info("Article, %s, has no blocking issues or errors" % article.doi)
        return True
    logger.info("Article, %s, has blocking issues or errors" % article.doi)
    return False
