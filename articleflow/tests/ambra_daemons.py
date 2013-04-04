from django.test import TestCase
from articleflow.daemons.transition_tasks import *
from articleflow.models import *
from articleflow.daemons.ambra_query import *

class TransitionTasksTestCase(TestCase):
    '''
    art 1:  pone.0058985
            pulled_article should be 'Pulled' in AI, but
            ingested or pubbed on stage
    art 2:  pone.0059284
            Same
    art 3:  pone.0060568
            Same
            
    
    '''
    
    fixtures = ['initial_data.json', 'transitions_testdata.json']

    def setUp(self):
        self.stage_c = AmbraStageConnection()
        #self.live_c = AmbraProdConnection()

    def tearDown(self):
        del self.stage_c
        #del self.live_c

    def test_assign_ingested_article(self):
        # art 1
        pulled_article = Article.objects.get(doi='pone.0058985')
        assign_ingested_article(pulled_article, self.stage_c)
        ingested_state = State.objects.get(name='Ingested')
        self.assertEqual(pulled_article.current_state, ingested_state)

    def test_assign_ingested(self):
        assign_ingested(self.stage_c)
        ingested_state = State.objects.get(name='Ingested')
        # art 2
        art_2 = Article.objects.get(doi='pone.0059284')
        # art 3
        art_3 = Article.objects.get(doi='pone.0060568')
        self.assertEqual(art_2.current_state, ingested_state)
        self.assertEqual(art_3.current_state, ingested_state)
        
