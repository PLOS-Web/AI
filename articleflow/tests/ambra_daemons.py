import datetime

from django.test import TestCase
from articleflow.daemons.transition_tasks import *
from articleflow.models import *
from articleflow.daemons.ambra_query import *

class TransitionTasksTestCase(TestCase):
    '''
    art 1:  pone.0058985
            pulled_article should be 'Pulled' in AI, but
            ingested or pubbed on stage
            pubdate > 3 days out
    art 2:  pone.0059284
            Same. pubdate = 3 days out
    art 3:  pone.0060568
            Same. pubdate < 3 days out
    art 4:  pone.01
            Ingested
    art 5:  pone.02
            Ingested. Should move to Needs web corrections
            
    
    '''
    
    fixtures = ['initial_data.json', 'transitions_testdata.json']

    def setUp(self):
        self.stage_c = AmbraStageConnection()
        today = datetime.date.today()
        self.art_1 = Article.objects.get(doi='pone.0058985')
        self.art_2 = Article.objects.get(doi='pone.0059284')
        self.art_3 = Article.objects.get(doi='pone.0060568')
        self.art_1.pubdate = today
        self.art_2.pubdate = add_workdays(today, 1)        
        self.art_3.pubdate = add_workdays(today, 3)
        self.art_1.save()
        self.art_2.save()
        self.art_3.save()
        #self.live_c = AmbraProdConnection()

    def tearDown(self):
        del self.stage_c
        #del self.live_c

    def test_assign_ingested_article(self):
        # art 1
        pulled_article = self.art_1
        assign_ingested_article(pulled_article, self.stage_c)
        ingested_state = State.objects.get(name='Ingested')
        self.assertEqual(pulled_article.current_state, ingested_state)

    def test_assign_ingested(self):
        assign_ingested(self.stage_c)
        ingested_state = State.objects.get(name='Ingested')
        art_1 = Article.objects.get(doi='pone.0058985')
        # art 2
        art_2 = Article.objects.get(doi='pone.0059284')
        # art 3
        art_3 = Article.objects.get(doi='pone.0060568')
        self.assertEqual(art_1.current_state, ingested_state)
        self.assertEqual(art_2.current_state, ingested_state)
        self.assertEqual(art_3.current_state, ingested_state)

    def test_assign_ready_for_qc_article(self):
        arts = Article.objects.all()
        for a in arts:
            print(a.doi, a.current_state)
        art_4 = Article.objects.get(doi='pone.01')
        assign_ready_for_qc_article(art_4) 
        art_4 = Article.objects.get(doi='pone.01')
        ready_for_qc_state = State.objects.get(name='Ready for QC (CW)')
        self.assertEqual(art_4.current_state, ready_for_qc_state)

        art_5 = Article.objects.get(doi='pone.02')
        assign_ready_for_qc_article(art_5)
        art_5 = Article.objects.get(doi='pone.02')
        web_corrections_state = State.objects.get(name='Needs Web Corrections (CW)')
        self.assertEqual(art_5.current_state, web_corrections_state)

    def test_assign_ready_for_qc(self):
        assign_ready_for_qc()

        art_4 = Article.objects.get(doi='pone.01')
        ready_for_qc_state = State.objects.get(name='Ready for QC (CW)')
        self.assertEqual(art_4.current_state, ready_for_qc_state)

        art_5 = Article.objects.get(doi='pone.02')
        web_corrections_state = State.objects.get(name='Needs Web Corrections (CW)')
        self.assertEqual(art_5.current_state, web_corrections_state)
        
