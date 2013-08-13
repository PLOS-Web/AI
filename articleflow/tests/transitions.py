from datetime import datetime, timedelta, date

from articleflow.daemons.transition_tasks import *
from django.test import TestCase

from articleflow.models import Article, State, ArticleState, Typesetter

class TransitionTasksTestCaseNoAmbra(TestCase):
    fixtures = ['initial_data.json', 'articleflow/tests/transitions_seed.json']

    def setUp(self):
        # merops
        self.art_1 = Article.objects.get(doi='pone.0000001')
        self.art_2 = Article.objects.get(doi='pone.0000002')
        # CW
        self.art_3 = Article.objects.get(doi='pone.0000003')
        self.art_4 = Article.objects.get(doi='pone.0000004')

        self.s_ingested = State.objects.get(unique_name='ingested')
        self.s_wc_cw = State.objects.get(unique_name='needs_web_corrections_cw')
        self.s_wc_merops = State.objects.get(unique_name='needs_web_corrections_merops')        
        self.s_urg_wc_cw = State.objects.get(unique_name='urgent_web_corrections_cw')
        self.s_urg_wc_merops = State.objects.get(unique_name='urgent_web_corrections_merops')

        self.s_qc_cw = State.objects.get(unique_name='ready_for_qc_cw')
        self.s_qc_merops = State.objects.get(unique_name='ready_for_qc_merops')

        ArticleState(article=self.art_1, state=self.s_ingested).save()
        ArticleState(article=self.art_2, state=self.s_ingested).save()
        ArticleState(article=self.art_3, state=self.s_ingested).save()
        ArticleState(article=self.art_4, state=self.s_ingested).save()

        self.t_cw = Typesetter.objects.get(name='CW')
        self.t_merops = Typesetter.objects.get(name='Merops')

    def test_no_typesetter_switch(self):
        ArticleState(article=self.art_1, state=self.s_wc_merops).save()
        ArticleState(article=self.art_1, state=self.s_ingested).save()
        
        assign_ready_for_qc()
        # No switch, should revert to web corrections
        self.art_1 = Article.objects.get(doi='pone.0000001')
        self.assertEqual(self.art_1.current_state, self.s_wc_merops)

    def test_typesetter_switch(self):
        ArticleState(article=self.art_1, state=self.s_wc_merops).save()
        ArticleState(article=self.art_1, state=self.s_ingested).save()

        # Switch to CW
        self.art_1.typesetter = self.t_cw
        self.art_1.save()

        # Switched, should go to CW QC
        ArticleState(article=self.art_1, state=self.s_ingested).save()
        assign_ready_for_qc()
        self.art_1 = Article.objects.get(doi='pone.0000001')
        self.assertEqual(self.art_1.current_state, self.s_qc_cw)

    def test_urgent_web_corrections(self):
        # CW
        ArticleState(article=self.art_3, state=self.s_wc_cw).save()
        pubdate = add_workdays(datetime.utcnow(), 3)
        self.art_3.pubdate = pubdate
        self.art_3.save()

        assign_urgent_corrections(2)
        self.art_3 = Article.objects.get(doi='pone.0000003')
        self.assertEqual(self.art_3.current_state, self.s_wc_cw)

        pubdate = add_workdays(datetime.utcnow(), 1)
        self.art_3.pubdate = pubdate
        self.art_3.save()

        assign_urgent_corrections(2)
        self.art_3 = Article.objects.get(doi='pone.0000003')
        self.assertEqual(self.art_3.current_state, self.s_urg_wc_cw)
    
        # Merops
        ArticleState(article=self.art_1, state=self.s_wc_merops).save()
        pubdate = add_workdays(datetime.utcnow(), 3)
        self.art_1.pubdate = pubdate
        self.art_1.save()

        assign_urgent_corrections(2)
        self.art_1 = Article.objects.get(doi='pone.0000001')
        self.assertEqual(self.art_1.current_state, self.s_wc_merops)

        pubdate = add_workdays(datetime.utcnow(), 1)
        self.art_1.pubdate = pubdate
        self.art_1.save()

        assign_urgent_corrections(2)
        self.art_1 = Article.objects.get(doi='pone.0000001')
        self.assertEqual(self.art_1.current_state, self.s_urg_wc_merops)
