from django.test import TestCase
from articleflow.daemons.transition_tasks import *
from articleflow.models import *
from ambra_query import *

class TransitionTasksTestCase(TestCase):
    '''
    art 1:  pone.0058985
            pulled_article should be 'Pulled' in AI, but
            ingested or pubbed on stage
    
    '''
    
    fixtures = ['transitions_testdata.json']

    def setUp():
        self.stage_c = AmbraStageConnection()
        self.live_c = AmbraProdConnection()

    def tearDown():
        del self.stage_c
        del self.live_c

    def test_assign_ingested_doi(self):
        # art 1
        pulled_article = Article.object.get(doi='pone.0058985')
        assign_ingested_doi(pulled_article, self.stage_c)
        ingested_state = State.objects.get(name='ingested')
        assertEqual(pulled_article.current_state, ingested_state)
