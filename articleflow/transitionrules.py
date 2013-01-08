from articleflow.models import Article
from issues.models import Issue, IssueStatus
from errors.models import Error, ErrorStatus

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

    for i in article.issues:
        if not ready_to_ignore(i):
            open_issues += 1
    
    for e in article.errors:
        if not ready_to_ignore(i):
            open_errors += 1

    return {
        'open_issues': open_issues,
        'open_errors': open_errors,
        }

def article_no_open_items(article):
    items = article_count_open_items(article)
    if (items.open_issues == 0 and items.open_errors == 0):
        return True
    return False
