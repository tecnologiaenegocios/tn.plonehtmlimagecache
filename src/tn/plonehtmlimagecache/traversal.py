from five import grok
from tn.plonehtmlimagecache.interfaces import ICacheManager
from zope.location.interfaces import LocationError
from zope.publisher.interfaces import IRequest
from zope.traversing.interfaces import ITraversable

import zope.interface
import zope.component


class DefaultTraverser(grok.MultiAdapter):
    """The default traverser.

    Allows traversal to /++tn_plonehtmlimagecache++<name>.
    """

    grok.adapts(zope.interface.Interface, IRequest)
    grok.implements(ITraversable)
    grok.name("tn_plonehtmlimagecache")

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def traverse(self, name, remaining):
        if name == 'cache':
            return zope.component.getUtility(ICacheManager)
        raise LocationError, name
