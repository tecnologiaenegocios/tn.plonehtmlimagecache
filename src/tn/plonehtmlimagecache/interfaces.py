from tn.plonehtmlimagecache import _

import zope.container.interfaces
import zope.interface
import zope.publisher.interfaces.browser
import zope.schema
import zope.sendmail


class ICache(zope.container.interfaces.IContainer):
    """A container used for caching.
    """


class IContextKeys(zope.interface.Interface):
    """An object that keeps track of which Keys are used in which contexts.
    """

    def link(key, context):
        """Establish a connection between the context and the key.

        If the connection is already established, nothing is done.
        """

    def unlink(key, context):
        """Unlink a previously established connection between the context and
        the key.

        If the connection was never set before, nothing is done.
        """

    def unlinkKey(key):
        """Unlink the given key from all contexts.
        """

    def unlinkContext(context):
        """Unlink the given context from all keys.
        """

    def isLinked(key, context):
        """Return True if the given context and key are linked.
        """

    def __contains__(key):
        """Return True if the key is linked with some context, False
        otherwise.
        """


class ICacheManager(zope.interface.Interface):
    """A cache manager.
    """

    def add(key, context, value):
        """Add the value to the cache and associate it with the given context.

        Replace the value if the key is already in use.
        """

    def remove(key, context):
        """Disassociate the key with the given context.

        If the key is left associated with no other context, remove the value
        from the cache.

        Raise KeyError if the key is invalid.
        """

    def __getitem__(key):
        """Return the value associated with the given key.

        Raise KeyError if the key is invalid.
        """

    def __contains__(key):
        """Return True if the given key exists in the cache, False otherwise.
        """


class ICacheKeys(zope.interface.Interface):
    """A converter between a external resource URL and a cache key.

    A component implementing this interface should hold the folowing
    invariants:

    component.getURL(component.getKey(original_url)) == original_url
    component.getKey(component.getURL(original_key)) == original_key
    """

    def getKey(url):
        """Return the key associated with the given URL.

        The key should not contain any character which may be
        considered a path separator by Zope ('/').
        """

    def getURL(key):
        """Return the URL associated with the given key.
        """


class ICacheRequest(zope.interface.Interface):
    """Marker interface for the request when it traverses through the cache.
    """


class IHTMLAttribute(zope.interface.Interface):
    """Provides a `html` attribute.

    Regardless of the encoding of the HTML document in the attribute,
    it is a unicode string.  It is responsibility of the objects that
    will later process this HTML to strip out (or ignore) any meta
    encoding tags and to provide those desired if converting to a byte
    string.
    """

    html = zope.schema.TextLine(title=_(u'HTML'))


class IHTMLImageCacheable(IHTMLAttribute):
    """An object which can have its external images collected and cached.
    """

    save_images_locally = zope.schema.Bool(title=_(u'Save images locally'))


class IPossibleHTMLImageCacheable(zope.interface.Interface):
    """Marker interface for objects which don't provide IHTMLImageCacheable
    directly, but can be adapted to it.
    """


class IHTMLImageCacher(zope.interface.Interface):
    """Parses HTML and caches its referenced images.
    """

    context = zope.interface.Attribute(
        u'The content object to have images collected'
    )

    def update():
        """Update image URLs of the context.

        If `save_images_locally` in the context is `True`, external
        images are collected and eventually inserted into the cache.
        If it is `False`, image URLs are restored and images eventually
        are removed from the cache.
        """
