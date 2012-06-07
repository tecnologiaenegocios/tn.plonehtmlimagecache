from tn.plonehtmlimagecache import interfaces
from tn.plonehtmlimagecache.tests import base
from zope.intid.interfaces import IIntIds

import zope.component


class TestInstallation(base.TestCase):

    def test_intids_installed(self):
        utility = zope.component.queryUtility(IIntIds)
        self.assertTrue(utility is not None)

    def test_context_keys_utility_installed(self):
        utility = zope.component.queryUtility(interfaces.IContextKeys)
        self.assertTrue(utility is not None)

    def test_cache_utility_installed(self):
        utility = zope.component.queryUtility(interfaces.ICache)
        self.assertTrue(utility is not None)
