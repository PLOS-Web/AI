from ai import settings
from django.test import TestCase

from articleflow.daemons.merops_tasks import *
from articleflow.models import *

class MeropsTasksTestCase(TestCase):
    fixtures = ['initial_data.json']

    def setUp(self):
        self.a1 = Article(doi='pone.0000001')
        self.a1.save()
        r_state = State.objects.get(unique_name='ready_to_build_article_package')
        a_s = ArticleState(article=self.a1, state=r_state)
        a_s.save()

    def test_test(self):
        build_merops_packages()
