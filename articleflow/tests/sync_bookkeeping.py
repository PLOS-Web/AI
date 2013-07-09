
from django.test import TestCase

from django.conf import settings

from articleflow.models import ExternalSync, SyncHistory

import logging
logger = logging.getLogger('articleflow.tests')

class SyncTestCase(TestCase):
    def setUp(self):
        self.ext1 = ExternalSync(name='test1',
                                 source='source1')
        self.ext1.save()
        self.ext2 = ExternalSync(name='test2',
                                 source='source2')
        self.ext2.save()
        self.ext3 = ExternalSync(name='test3',
                                 source='source3')
        self.ext3.save()

    def test_start_stop(self):
        sync = self.ext1.start_sync()
        sync.complete()
        logger.debug(vars(sync))

    def test_is_done(self):
        sync = self.ext1.start_sync()
        self.assertFalse(sync.is_done())
        sync.complete()
        self.assertTrue(sync.is_done())        

    def test_latest_sync(self):
        s1 = self.ext1.start_sync()
        s1.complete()
        s2 = self.ext1.start_sync()
        s2.complete()
        self.assertEqual(s2, self.ext1.latest_sync)

        s3 = self.ext2.start_sync()
        s3.complete()
        self.assertEqual(s2, self.ext1.latest_sync)
        self.assertEqual(s3, self.ext2.latest_sync)
        
