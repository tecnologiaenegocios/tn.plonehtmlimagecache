from tn.plonehtmlimagecache.context_keys import ContextKeys
from zope.keyreference.interfaces import IKeyReference

import unittest
import zope.component
import zope.interface
import zope.keyreference.interfaces


class DummyKeyReference(object):
    zope.component.adapts(zope.interface.Interface)
    zope.interface.implements(IKeyReference)

    def __init__(self, obj):
        self.obj = obj

    def __hash__(self):
        return hash(self.obj)

    def __cmp__(self, other):
        return cmp(hash(self), hash(other))


class TestContextKeysUnit(unittest.TestCase):

    def setUp(self):
        self.context_keys = ContextKeys()
        self.sm = zope.component.globalregistry.getGlobalSiteManager()
        zope.component.provideAdapter(DummyKeyReference)

    def tearDown(self):
        self.sm.unregisterAdapter(DummyKeyReference)

    def test_link_key_with_context(self):
        context = object()
        self.context_keys.link('some key', context)
        self.assertTrue(self.context_keys.isLinked('some key', context))

    def test_link_key_with_other_context(self):
        context = object()
        self.context_keys.link('some key', context)
        self.assertTrue(not self.context_keys.isLinked('some key', object()))

    def test_link_other_key_with_context(self):
        context = object()
        self.context_keys.link('some other key', context)
        self.assertTrue(not self.context_keys.isLinked('some key', context))

    def test_link_same_context_and_key_twice(self):
        context = object()
        self.context_keys.link('some key', context)
        self.context_keys.link('some key', context)
        self.assertTrue(self.context_keys.isLinked('some key', context))

    def test_unlink_context_from_key(self):
        context = object()
        self.context_keys.link('some key', context)
        self.context_keys.unlink('some key', context)
        self.assertTrue(not self.context_keys.isLinked('some key', context))

    def test_unlink_context_from_key_which_werent_linked(self):
        context = object()
        self.context_keys.unlink('some key', context)
        self.assertTrue(not self.context_keys.isLinked('some key', context))

    def test_unlink_same_context_from_key_twice(self):
        context = object()
        self.context_keys.link('some key', context)
        self.context_keys.unlink('some key', context)
        self.context_keys.unlink('some key', context)
        self.assertTrue(not self.context_keys.isLinked('some key', context))

    def test_unlink_key(self):
        context1 = object()
        context2 = object()
        self.context_keys.link('some key', context1)
        self.context_keys.link('some key', context2)
        self.context_keys.unlinkKey('some key')
        self.assertTrue(not self.context_keys.isLinked('some key', context1))
        self.assertTrue(not self.context_keys.isLinked('some key', context2))

    def test_unlink_context(self):
        context = object()
        self.context_keys.link('some key', context)
        self.context_keys.link('some other key', context)
        self.context_keys.link('yet another key', context)
        self.context_keys.unlinkContext(context)
        self.assertTrue(not self.context_keys.isLinked('some key', context))
        self.assertTrue(not self.context_keys.isLinked('some other key',
                                                       context))
        self.assertTrue(not self.context_keys.isLinked('yet another key',
                                                       context))

    def test_uncontainment(self):
        self.assertTrue('some key' not in self.context_keys)

    def test_containment(self):
        context = object()
        self.context_keys.link('some key', context)
        self.assertTrue('some key' in self.context_keys)
        self.assertTrue('some other key' not in self.context_keys)

    def test_uncontainment_after_being_empty(self):
        context = object()
        self.context_keys.link('some key', context)
        self.context_keys.unlink('some key', context)
        self.assertTrue('some key' not in self.context_keys)

    def test_uncontainment_after_unlinking_key(self):
        self.context_keys.link('some key', object())
        self.context_keys.link('some key', object())
        self.context_keys.unlinkKey('some key')
        self.assertTrue('some key' not in self.context_keys)

    def test_uncontainment_after_unlinking_context(self):
        context = object()
        self.context_keys.link('some key', context)
        self.context_keys.link('some other key', context)
        self.context_keys.unlinkContext(context)
        self.assertTrue('some key' not in self.context_keys)
        self.assertTrue('some other key' not in self.context_keys)

    def test_unlink_all_with_unlinked_key(self):
        try:
            self.context_keys.unlinkKey('some key')
        except Exception as exc:
            self.fail(exc)

    def test_unlink_all_with_unlinked_context(self):
        try:
            self.context_keys.unlinkContext(object())
        except Exception as exc:
            self.fail(exc)

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
