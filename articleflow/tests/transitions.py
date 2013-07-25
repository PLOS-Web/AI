from articleflow.daemons.transition_tasks import *
from django.test import TestCase

from articleflow.models import Article, State, ArticleState

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
        self.s_qc_cw = State.objects.get(unique_name='ready_for_qc_cw')
        self.s_qc_merops = State.objects.get(unique_name='ready_for_qc_merops')

        ArticleState(article=self.art_1, state=self.s_ingested).save()
        ArticleState(article=self.art_2, state=self.s_ingested).save()
        ArticleState(article=self.art_3, state=self.s_ingested).save()
        ArticleState(article=self.art_4, state=self.s_ingested).save()

    def test_typesetter_switch(self):
        ArticleState(article=self.art_1, state=self.s_wc_merops).save()
        ArticleState(article=self.art_1, state=self.s_ingested).save()
        
        assign_ready_for_qc_article(self.art_1)
        self.assertEqual(self.art_1.current_state, self.s_qc_merops)
        
    def test_min(self):
        self.assertEqual(1,1)
