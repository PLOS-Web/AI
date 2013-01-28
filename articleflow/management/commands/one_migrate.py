import re

from django.core.management.base import BaseCommand, CommandError

import one_migration
from articleflow.models import Article, ArticleState, State, Journal
from errors.models import Error, ErrorSet


def get_journal_from_doi(doi):
    match = re.match('.*(?=\.)', doi)
    
    if not match:
        raise ValueError('Could not find a journal short_name in doi, %s' % doi)
    short_name = re.match('.*(?=\.)', doi).group(0)
    
    try:
        return Journal.objects.get(short_name=short_name)
    except Journal.DoesNotExist:
        raise ValueError("doi prefix, %s, does not match any known journal" % short_name)

def insert_articles(pulls):
    
    ariespull_state = State.objects.get(name="Ingested")
    for pull in pulls:
        get_journal_from_doi(pull['doi'])

        pubdate = pull['pubdate']
        if not pubdate:
            pubdate = '1900-01-01'

        # Create Article
        a, _ = Article.objects.get_or_create(doi=pull['doi'],
                                          pubdate=pubdate,
                                          journal=get_journal_from_doi(pull['doi'])
                                          )
        print a
        a.save()

        # Create Article State
        a_state = ArticleState(article=a,
                               state=ariespull_state,
                               created=pull['pulltime'])
        a_state.save()

        # Create Errorset from pull record
        es = ErrorSet(source=1,
                      article=a)
        es.save()

        for error in pull['errors']:
            e = Error(message=error,
                      level=1,
                      error_set=es)
            e.save()
        
        
class Command(BaseCommand):
    def handle(self, *args, **options):
        m = one_migration.GrabAT()
        pulls = m.get_pull_dois()
        insert_articles(pulls)
