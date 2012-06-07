from Products.CMFDefault.Document import Document
from plone.behavior.interfaces import IBehavior
from plone.behavior.interfaces import IBehaviorAssignable
from plone.directives.form import IFormFieldProvider
from tn.plonehtmlimagecache import behaviors
from tn.plonehtmlimagecache import interfaces
from tn.plonehtmlimagecache.tests import base
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.app.testing import placelesssetup

import stubydoo
import unittest
import zope.annotation
import zope.component
import zope.interface


def set_default_attr(obj, attr, default=None):
    if not hasattr(obj, attr):
        setattr(obj, attr, default)
    return getattr(obj, attr)


@zope.component.adapter(None)
@zope.interface.implementer(zope.annotation.interfaces.IAnnotations)
def annotations(context):
    return set_default_attr(context, '_annotations', dict())


class TestCase(unittest.TestCase):

    def setUp(self):
        placelesssetup.setUp(self)
        zope.component.provideAdapter(annotations)
        self.context = stubydoo.double()
        self.adapted = behaviors.HTMLImageCacheableFromContent(self.context)

    def tearDown(self):
        placelesssetup.tearDown()


class TestHTMLImageCacheableFromContentBehavior(TestCase):

    def test_behavior_provides_form_fields(self):
        self.assertTrue(IFormFieldProvider.providedBy(
            behaviors.IHTMLImageCacheableFromContent
        ))


class TestHTMLImageCacheableFromContentSaveImagesLocallyFlag(TestCase):

    def test_save_images_locally_defaults_to_false(self):
        self.assertFalse(self.adapted.save_images_locally)

    def test_save_images_locally_can_be_set_to_true(self):
        self.adapted.save_images_locally = True
        self.assertTrue(self.adapted.save_images_locally)

    def test_save_images_locally_is_persisted(self):
        self.adapted.save_images_locally = False
        self.adapted.save_images_locally = True

        new_adapted = behaviors.HTMLImageCacheableFromContent(self.context)

        self.assertTrue(new_adapted.save_images_locally)


class TestHTMLImageCacheableFromContentHTML(TestCase):

    def setUp(self):
        super(TestHTMLImageCacheableFromContentHTML, self).setUp()
        class HTMLAttribute(object):
            zope.component.adapts(None)
            zope.interface.implements(interfaces.IHTMLAttribute)
            def __init__(self, context): self.context = context
            def _set_html(self, value): self.context._html = value
            def _get_html(self):
                return set_default_attr(self.context, '_html', 'no-value')
            html = property(_get_html, _set_html)
        zope.component.provideAdapter(HTMLAttribute)

    def test_gets_html_from_adapter(self):
        self.assertEquals(self.adapted.html, 'no-value')

    def test_sets_html_to_adapter(self):
        self.adapted.html = 'other-value'

        self.assertEquals(self.adapted.html, 'other-value')


class TestHTMLImageCacheableFromContentBehaviorRegistration(base.TestCase):

    def afterSetUp(self):
        super(TestHTMLImageCacheableFromContentBehaviorRegistration, self).\
                afterSetUp()
        self.context = Document('document')
        zope.interface.alsoProvides(self.context, IAttributeAnnotatable)
        self.behavior_assignable_factory = None

        # This will enable the behavior for our document.
        class BehaviorAssignable(object):
            zope.component.adapts(Document)
            zope.interface.implements(IBehaviorAssignable)
            def __init__(self, context):
                self.context = context
            def supports(self, behavior_interface):
                return behavior_interface is \
                        behaviors.IHTMLImageCacheableFromContent
            def enumerate_behaviors(self):
                i = behaviors.IHTMLImageCacheableFromContent
                yield zope.component.queryUtility(IBehavior,
                                                  name=i.__identifier__)

        zope.component.provideAdapter(BehaviorAssignable)
        self.behavior_assignable_factory = BehaviorAssignable

    def beforeTearDown(self):
        zope.component.getGlobalSiteManager().\
                unregisterAdapter(self.behavior_assignable_factory)

    def test_behavior_is_registered(self):
        self.assertTrue(zope.component.queryUtility(
            IBehavior,
            name=behaviors.IHTMLImageCacheableFromContent.__identifier__
        ) is not None)

    def test_behavior_has_correct_marker(self):
        behavior = zope.component.queryUtility(
            IBehavior,
            name=behaviors.IHTMLImageCacheableFromContent.__identifier__
        )
        if behavior is None:
            self.fail('behavior not registered')
        else:
            self.assertTrue(behavior.marker is
                            interfaces.IPossibleHTMLImageCacheable)

    def test_behavior_is_usable(self):
        adapted = behaviors.IHTMLImageCacheableFromContent(self.context, None)
        self.assertTrue(adapted is not None)

    def test_adaptation_to_html_image_cacheable_uses_behavior(self):
        adapted = interfaces.IHTMLImageCacheable(self.context, None)
        self.assertTrue(interfaces.IHTMLImageCacheable.providedBy(adapted))

    def test_adaptation_to_html_image_cacheable_fails_if_cant_adapt_behavior(self):
        context = stubydoo.double()
        zope.interface.alsoProvides(context,
                                    interfaces.IPossibleHTMLImageCacheable)
        adapted = interfaces.IHTMLImageCacheable(context, None)
        self.assertTrue(adapted is None)
