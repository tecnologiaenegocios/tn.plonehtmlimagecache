from five import grok
from persistent.dict import PersistentDict
from plone.directives import form
from plone.supermodel import model
from tn.plonehtmlimagecache import _
from tn.plonehtmlimagecache import interfaces
from zope.annotation.interfaces import IAnnotations
from zope.annotation.interfaces import IAttributeAnnotatable

import zope.interface

HTML_IMAGE_CACHEABLE_KEY = 'tn.plonehtmlimagecache.html-image.cacheable'


class IHTMLImageCacheableFromContent(model.Schema,
                                     interfaces.IHTMLImageCacheable):

    form.fieldset(
        'image-caching',
        label=_(u'Image caching'),
        fields=('save_images_locally',),
    )

    form.omitted('html')


zope.interface.alsoProvides(IHTMLImageCacheableFromContent,
                            form.IFormFieldProvider)


apply = lambda f: f()


class HTMLImageCacheableFromContent(object):
    """Provides the behavior of being HTMLImage-cacheable to a generic content
    object.

    The HTML to be inspected and cached is provided and modified
    through an adapter from the content object to IHTMLAttribute.
    """

    zope.interface.implements(IHTMLImageCacheableFromContent)
    zope.component.adapts(IAttributeAnnotatable)

    def __init__(self, context):
        self.context = context
        self._annotations = None

    @apply
    def save_images_locally():
        def get(self):
            return self.annotations().get('save_images_locally')

        def set(self, value):
            self.annotations()['save_images_locally'] = value
        return property(get, set)

    @apply
    def html():
        def get(self):
            return interfaces.IHTMLAttribute(self.context).html

        def set(self, value):
            interfaces.IHTMLAttribute(self.context).html = value
        return property(get, set)

    def annotations(self):
        if self._annotations:
            return self._annotations
        annotations = IAnnotations(self.context)
        values = annotations.get(HTML_IMAGE_CACHEABLE_KEY, None)
        if values is None:
            values = annotations[HTML_IMAGE_CACHEABLE_KEY] = PersistentDict()
        self._annotations = values
        return values


@grok.adapter(interfaces.IPossibleHTMLImageCacheable)
@grok.implementer(interfaces.IHTMLImageCacheable)
def html_image_cacheable(context):
    # By returning None here in case the behavior is not active, we tell ZCA
    # that this adapter cannot be provided and also should fail.

    # We could provide our implementation directly, but we can't be sure this
    # will work for everything providing IPossibleHTMLImageCacheable.
    return IHTMLImageCacheableFromContent(context, None)
