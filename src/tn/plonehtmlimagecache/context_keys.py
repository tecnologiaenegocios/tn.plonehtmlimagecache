from five import grok
from persistent import Persistent
from persistent.dict import PersistentDict
from tn.plonehtmlimagecache.interfaces import IContextKeys
from zope.keyreference.interfaces import IKeyReference


class PersistentSet(Persistent):
    """Almost a set, but can be persisted.

    The only behavior of a 'set' implemented here is the uniqueness of
    its elements.  No additional methods (like union or intersection)
    are implemented.
    """

    def __init__(self):
        self.inner_set = set()

    def add(self, value):
        self.inner_set.add(value)
        self._p_changed = True

    def discard(self, value):
        if value in self.inner_set:
            self._p_changed = True
        self.inner_set.discard(value)

    def __contains__(self, value):
        return value in self.inner_set

    def __nonzero__(self):
        return bool(self.inner_set)


class ContextKeys(Persistent):
    grok.implements(IContextKeys)

    def __init__(self):
        self._items = PersistentDict()

    def link(self, key, context):
        id = hash(IKeyReference(context))
        ids = self._items.setdefault(key, PersistentSet())
        ids.add(id)

    def unlink(self, key, context):
        id = hash(IKeyReference(context))
        ids = self._items.setdefault(key, PersistentSet())
        ids.discard(id)
        if not ids:
            del self._items[key]

    def unlinkKey(self, key):
        if key in self._items:
            del self._items[key]

    def unlinkContext(self, context):
        id = hash(IKeyReference(context))
        keys_removed = set()
        for key, ids in self._items.items():
            ids.discard(id)
            if not ids:
                keys_removed.add(key)
        for key in keys_removed:
            del self._items[key]
        return keys_removed

    def isLinked(self, key, context):
        id = hash(IKeyReference(context))
        return id in self._items.get(key, set())

    def __contains__(self, key):
        return key in self._items
