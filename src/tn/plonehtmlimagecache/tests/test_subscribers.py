from Products.ATContentTypes.content.document import ATDocument
from Products.ATContentTypes.interfaces import IATDocument
from tn.plonehtmlimagecache import interfaces
from tn.plonehtmlimagecache.tests import base
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent

import lxml.html
import os.path
import re
import zope.component
import zope.interface


apply = lambda fn: fn()

class HTMLHandler(object):
    zope.component.adapts(IATDocument)
    zope.interface.implements(interfaces.IHTMLImageCacheable)
    def __init__(self, context):
        self.context = context
        self.save_images_locally = True
    @apply
    def html():
        def get(self): return self.context.getText()
        def set(self, html):
            tree = lxml.html.document_fromstring(html)
            self.context.setText(''.join(lxml.html.tostring(e) for e in
                                         tree.body))
        return property(get, set)


class TestCaching(base.TestCase):

    def afterSetUp(self):
        zope.interface.classImplements(ATDocument,
                                       interfaces.IPossibleHTMLImageCacheable)
        zope.component.provideAdapter(HTMLHandler)

        self.test_img = os.path.join(os.path.dirname(__file__), 'test.png')
        with open(self.test_img) as f:
            self.img_binary = f.read()

        self.loginAsPortalOwner()

    def beforeTearDown(self):
        zope.component.getGlobalSiteManager().unregisterAdapter(HTMLHandler)

    def add_document(self):
        self.portal.invokeFactory(
            id='document',
            title='Document',
            text='<p>Image: <img src="file://%s" alt="" /></p>' % self.test_img,
            type_name='Document'
        )

    def del_document(self):
        self.portal._delObject('document')

    def test_image_cached_on_add(self):
        self.add_document()

        current_content = self.portal['document'].getText()
        tree = lxml.html.fragment_fromstring(current_content)
        current_url = tree.find('img').attrib['src']
        internal_url_re = re.compile(
            r'^%s/\+\+tn_plonehtmlimagecache\+\+cache/[^/]+$' %
            self.portal.absolute_url()
        )
        self.assertTrue(internal_url_re.match(current_url) is not None)

    def test_image_cached_on_edit(self):
        self.add_document()
        self.portal['document'].setText(
            '<p style="background-image:url(file://%s);">Image</p>' % self.test_img
        )
        notify(ObjectModifiedEvent(self.portal['document']))

        current_content = self.portal['document'].getText()
        tree = lxml.html.fragment_fromstring(current_content)
        current_url = tree.attrib['style']
        internal_url_re = re.compile(
            r'^background-image:url\(%s/\+\+tn_plonehtmlimagecache\+\+cache/[^/]+\);$' %
            self.portal.absolute_url()
        )
        self.assertTrue(internal_url_re.match(current_url) is not None)

    def test_cache_cleared(self):
        self.add_document()
        self.del_document()

        self.assertEquals(len(zope.component.getUtility(interfaces.ICache)), 0)
