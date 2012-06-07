from tn.plonehtmlimagecache.interfaces import ICacheManager
from tn.plonehtmlimagecache.traversal import DefaultTraverser
from zope.location.interfaces import LocationError

import unittest
import zope.component


class TestDefaultTraverser(unittest.TestCase):

    def setUp(self):
        self.cache_manager = object()
        self.site = object()
        zope.component.provideUtility(self.cache_manager, ICacheManager)
        self.traverser = DefaultTraverser(self.site, 'request')

    def tearDown(self):
        sm = zope.component.globalregistry.getGlobalSiteManager()
        sm.unregisterUtility(self.cache_manager, ICacheManager)

    def test_accessing_image_cache(self):
        self.assertTrue(self.traverser.traverse('cache', []) is
                        self.cache_manager)

    def test_accessing_something_else(self):
        self.assertRaises(LocationError, self.traverser.traverse,
                          'something else', [])
