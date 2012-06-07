from five import grok
from tn.plonehtmlimagecache import interfaces
from zope.container.folder import Folder
from zope.publisher.interfaces import IRequest
from zope.publisher.interfaces import IPublishTraverse
from zope.publisher.interfaces import NotFound

import base64
import re
import zope.interface
import zope.component


class Cache(Folder):
    grok.implements(interfaces.ICache)


class CacheManager(grok.GlobalUtility):
    grok.implements(interfaces.ICacheManager)

    def add(self, key, context, value):
        if not key in self.cache:
            self.cache[key] = value
        self.context_keys.link(key, context)

    def remove(self, key, context):
        self.context_keys.unlink(key, context)

        if key not in self.context_keys and key in self.cache:
            del self.cache[key]

    def removeAll(self, context):
        keys_removed = self.context_keys.unlinkContext(context)
        for key in keys_removed:
            del self.cache[key]

    def __getitem__(self, key):
        return self.cache[key]

    def __contains__(self, key):
        return key in self.cache

    @property
    def cache(self):
        return zope.component.getUtility(interfaces.ICache)

    @property
    def context_keys(self):
        return zope.component.getUtility(interfaces.IContextKeys)


class CacheManagerTraverser(grok.MultiAdapter):
    """Traverse to a cache manager.
    """
    grok.adapts(interfaces.ICacheManager, IRequest)
    grok.implements(IPublishTraverse)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def publishTraverse(self, request, key):
        if key in self.context:
            zope.interface.alsoProvides(request, interfaces.ICacheRequest)
            return self.context[key]
        cache_keys = zope.component.getUtility(interfaces.ICacheKeys)
        url = cache_keys.getURL(key)
        if url:
            request.response.redirect(url)
        else:
            raise NotFound(self, key, request=request)


url_has_extension = re.compile('^.*\.[^./]+$').match
class CacheKeys(grok.GlobalUtility):
    grok.implements(interfaces.ICacheKeys)

    def getKey(self, url):
        ext = url.split('.')[-1] if url_has_extension(url) else ''
        key = '~' + base64.urlsafe_b64encode(url).replace('=', '') + '.' + ext
        return key.strip('.')

    def getURL(self, key):
        url = key.split('.')[0][1:] if '.' in key else key
        missing_pad_chars = len(url) % 4
        url += missing_pad_chars * '='
        return base64.urlsafe_b64decode(url)
