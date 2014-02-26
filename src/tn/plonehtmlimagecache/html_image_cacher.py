from five import grok
from plone.namedfile import NamedBlobImage
from plone.namedfile.interfaces import INamedBlobImage
from plone.namedfile.utils import safe_basename, set_headers, stream_data
from tn.plonehtmlimagecache import interfaces
from zope.component.hooks import getSite
from zope.container.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.lifecycleevent.interfaces import IObjectRemovedEvent

import lxml.html
import re
import urllib
import urllib2
import urlparse
import zope.component
import zope.publisher

image_url_re = re.compile(r'^.*\.(jpg|gif|png|bmp|ico)$')
scheme_re    = re.compile(r'^[^/]+://')


class HTMLImageCacher(grok.Adapter):
    grok.context(interfaces.IPossibleHTMLImageCacheable)
    grok.implements(interfaces.IHTMLImageCacher)

    def __init__(self, context):
        self.context = context
        self.cacheable = interfaces.IHTMLImageCacheable(context)
        self.tree = lxml.html.document_fromstring(self.cacheable.html)
        self.url_opener = urllib2.build_opener()
        self.url_opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
        self.image_blob_factory = NamedBlobImage

    def update(self):
        if self.cacheable.save_images_locally:
            self.cacheable.html = self.cache()
        else:
            self.cacheable.html = self.restore()

    def cache(self):
        portal = getSite()
        portal_url  = portal.absolute_url()
        prefix = portal_url + '/++tn_plonehtmlimagecache++cache/'
        cache_manager = zope.component.getUtility(interfaces.ICacheManager)
        cache_keys = zope.component.getUtility(interfaces.ICacheKeys)

        cache_manager.removeAll(self.context)

        def replace_link(link):
            if not match(link):
                return link

            try:
                f = self.url_opener.open(link)
            except urllib2.HTTPError:
                return link

            path = urlparse.urlparse(link).path
            filename = unicode(urllib.quote(safe_basename(path)))

            key = cache_keys.getKey(link)
            value = self.image_blob_factory(f.read(), filename=filename)

            cache_manager.add(key, self.context, value)
            return prefix + urllib.quote(key, safe='')

        def match(url):
            return is_external(url) and is_image(url)

        def is_external(url):
            return (not url.startswith(portal_url) and scheme_re.match(url))

        def is_image(url):
            return image_url_re.match(url)

        self.tree.rewrite_links(replace_link)

        return lxml.html.tostring(self.tree,
                                  pretty_print=True,
                                  encoding=unicode)

    def restore(self):
        portal = getSite()
        portal_url  = portal.absolute_url()
        cache_manager = zope.component.getUtility(interfaces.ICacheManager)
        cache_keys = zope.component.getUtility(interfaces.ICacheKeys)
        prefix = portal_url + '/++tn_plonehtmlimagecache++cache/'

        def replace_link(link):
            if not match(link):
                return link

            key = urllib.unquote(link[len(prefix):])
            cache_manager.remove(key, self.context)
            return cache_keys.getURL(key)

        def match(url):
            return url.startswith(prefix)

        self.tree.rewrite_links(replace_link)

        return lxml.html.tostring(self.tree,
                                  pretty_print=True,
                                  encoding=unicode)


class CachedImagePublisher(grok.MultiAdapter):
    grok.adapts(INamedBlobImage, interfaces.ICacheRequest)
    grok.implements(zope.publisher.interfaces.browser.IBrowserPublisher)

    def __init__(self, file, request):
        self.context = file
        self.request = request

    def publishTraverse(self, request, name):
        # We can't traverse into an image file.
        raise zope.publisher.interfaces.NotFound(self, name, request=request)

    def browserDefault(self, request):
        """Set the headers of the response to allow serving the image.
        """
        set_headers(self.context, request.response, filename=None)
        return (stream_data(self.context), ())


def update_cache(context, event):
    interfaces.IHTMLImageCacher(context).update()
    context.reindexObject()

@grok.subscribe(interfaces.IPossibleHTMLImageCacheable, IObjectAddedEvent)
def doCachingOnAdd(context, event):
    update_cache(context, event)

@grok.subscribe(interfaces.IPossibleHTMLImageCacheable, IObjectModifiedEvent)
def doCachingOnModify(context, event):
    update_cache(context, event)

@grok.subscribe(interfaces.IPossibleHTMLImageCacheable, IObjectRemovedEvent)
def removeItemsFromCache(context, event):
    cache_manager = zope.component.getUtility(interfaces.ICacheManager)
    cache_manager.removeAll(context)
