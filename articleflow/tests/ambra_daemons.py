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
    art 2:  pone.0059284
            same ^
    art 3:  pone.0060568
            same ^
    art 4:  pone.01
            Ingested
    art 5:  pone.02
            Ingested. Should move to Needs web corrections
    art 6:  pone.03
            Ready for QC. Pubdate = today
    art 7:  pone.04
            Ready for QC. Pubdate = 3 days from now
    art 8:  pone.05
            Ready for QC. Pubdate = 4 days from now
    art 9:  pone.06
            Ready for QC. Pubdate = yesterday
    art 10: pone.0059893
            Ready to publish. Pubbed on stage            
    
    '''
    
    fixtures = ['initial_data.json', 'transitions_testdata.json']

    def setUp(self):
        arts = Article.objects.all()
        for a in arts:
            print(a.doi)
        self.stage_c = AmbraStageConnection()
        today = datetime.date.today()
        self.urgent_threshold = 3
        self.art_6 = Article.objects.get(doi='pone.03')
        self.art_7 = Article.objects.get(doi='pone.04')
        self.art_8 = Article.objects.get(doi='pone.05')
        self.art_9 = Article.objects.get(doi='pone.06')
        self.art_6.pubdate = today
        self.art_7.pubdate = add_workdays(today, 1)        
        self.art_8.pubdate = add_workdays(today, 4)
        self.art_9.pubdate = today - datetime.timedelta(days=1)
        self.art_6.save()
        self.art_7.save()
        self.art_8.save()
        self.art_9.save()
        #self.live_c = AmbraProdConnection()

    def tearDown(self):
        del self.stage_c
        #del self.live_c

    def test_add_workdays(self):
        a_monday = datetime.date(year=2013,month=4,day=1)
        a_monday_0 = add_workdays(a_monday, 0)
        self.assertEqual(a_monday_0, a_monday)

        a_monday = datetime.date(year=2013,month=4,day=1)
        a_monday_3 = add_workdays(a_monday, 3)
        self.assertEqual(a_monday_3, datetime.date(year=2013,month=4,day=4))

        a_wednesday = datetime.date(year=2013,month=4,day=3)
        a_wednesday_3 = add_workdays(a_wednesday, 3)
        self.assertEqual(a_wednesday_3, datetime.date(year=2013,month=4,day=8))

        a_friday = datetime.date(year=2013,month=4,day=5)
        a_friday_3 = add_workdays(a_friday, 3)
        self.assertEqual(a_friday_3, datetime.date(year=2013,month=4,day=10))

        a_saturday = datetime.date(year=2013,month=4,day=6)
        a_saturday_3 = add_workdays(a_saturday, 3)
        self.assertEqual(a_saturday_3, datetime.date(year=2013,month=4,day=10))

        a_saturday = datetime.date(year=2013,month=4,day=6)
        a_saturday_0 = add_workdays(a_saturday, 0)
        self.assertEqual(a_saturday_0, a_saturday)


    def test_assign_ingested_article(self):
        # art 1
        pulled_article = Article.objects.get(doi='pone.0058985')
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

    def test_assign_urgent_article(self):
        urgent_state = State.objects.get(name='Urgent QC (CW)')
        ready_for_qc_state = State.objects.get(name='Ready for QC (CW)')

        art_6 = Article.objects.get(doi='pone.03')
        assign_urgent_article(art_6, self.urgent_threshold)
        art_6 = Article.objects.get(doi='pone.03')
        self.assertEqual(art_6.current_state, urgent_state)
        
        art_7 = Article.objects.get(doi='pone.04')
        assign_urgent_article(art_7, self.urgent_threshold)
        art_7 = Article.objects.get(doi='pone.04')
        self.assertEqual(art_7.current_state, urgent_state)

        art_8 = Article.objects.get(doi='pone.05')
        assign_urgent_article(art_8, self.urgent_threshold)
        art_8 = Article.objects.get(doi='pone.05')
        self.assertEqual(art_8.current_state, ready_for_qc_state)

        art_9 = Article.objects.get(doi='pone.06')
        assign_urgent_article(art_9, self.urgent_threshold)
        art_9 = Article.objects.get(doi='pone.06')
        self.assertEqual(art_9.current_state, urgent_state)

    def test_assign_urgent(self):
        assign_urgent(self.urgent_threshold)

        urgent_state = State.objects.get(name='Urgent QC (CW)')
        ready_for_qc_state = State.objects.get(name='Ready for QC (CW)')

        art_6 = Article.objects.get(doi='pone.03')
        self.assertEqual(art_6.current_state, urgent_state)
        
        art_7 = Article.objects.get(doi='pone.04')
        self.assertEqual(art_7.current_state, urgent_state)

        art_8 = Article.objects.get(doi='pone.05')
        self.assertEqual(art_8.current_state, ready_for_qc_state)

        art_9 = Article.objects.get(doi='pone.06')
        self.assertEqual(art_9.current_state, urgent_state)

    def test_published_stage_article(self):        
        art_10 = Article.objects.get(doi='pone.0059893')
        assign_published_stage_article(art_10, self.stage_c)
        published_on_stage_state = State.objects.get(name='Published on Stage')
        self.assertEqual(art_10.current_state, published_on_stage_state)

    def test_published_stage(self):
        assign_published_stage(self.stage_c)
        published_on_stage_state = State.objects.get(name='Published on Stage')
        art_10 = Article.objects.get(doi='pone.0059893')
        self.assertEqual(art_10.current_state, published_on_stage_state)
