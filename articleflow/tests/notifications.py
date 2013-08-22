from django.test import TestCase

from django.contrib.auth.models import User

from articleflow.models import Article, ArticleState, State, Transition
from notification.models import Notice

import logging
logger = logging.getLogger(__name__)

class NotificationsTestCase(TestCase):
    fixtures = ['initial_data.json', 'articleflow/tests/transitions_seed.json']

    def setUp(self):
        self.effecting_user = User(username='other-jlabarba', email='jlabarba@plos.org')
        self.recipient_user = User(username='jlabarba', email='jlabarba@plos.org')
        self.recipient_user.save()

    def test_send_back_to_production(self):
        t = Transition.objects.get(unique_name='send_back_to_production_cw')
        a = Article.objects.get(doi='pone.0000001')

        web_corrections = State.objects.get(unique_name = 'needs_web_corrections_cw')
        arts = ArticleState(article=a, state=web_corrections)
        arts.save()

        a.execute_transition(t, self.effecting_user, self.recipient_user)

        self.assertEqual(Notice.objects.count(), 1)
        logger.debug(Notice.objects.all())

    def test_urgent_corrections(self):
        pass
