from stubydoo import double, stub, expect, assert_expectations
from StringIO import StringIO
from tn.plonehtmlimagecache import html_image_cacher
from tn.plonehtmlimagecache import interfaces
from zope.app.testing import placelesssetup
from zope.component import getGlobalSiteManager
try:
    from zope.component.hooks import setSite
except ImportError:
    from zope.site.hooks import setSite

import inspect
import lxml
import unittest
import urllib2
import zope.component


class DummyCacheManager(object):
    def __init__(self):
        self._items = {}
    def add(self, key, context, value):
        self._items.setdefault(context, {})[key] = value
    def remove(self, key, context):
        if context in self._items:
            if key in self._items[context]:
                del self._items[key]
    def removeAll(self, context):
        if context in self._items:
            del self._items[context]


cache_manager = DummyCacheManager()
cache_keys = double(getKey=lambda *a:'key', getURL=lambda *a:'url')
portal = double(absolute_url=lambda self: 'http://internal.com',
                getSiteManager=lambda self: getGlobalSiteManager())
url_opener = double(open=lambda self, link: StringIO())
img_blob_factory = lambda s, filename=None: double(s=s, filename=filename)

apply = lambda fn: fn()

class Cacheable(object):
    zope.component.adapts(interfaces.IPossibleHTMLImageCacheable)
    zope.interface.implements(interfaces.IHTMLImageCacheable)
    def __init__(self, context): self.context = context
    @apply
    def html():
        def get(self): return self.context.original_html
        def set(self, value): self.context.original_html = value
        return property(get, set)
    @apply
    def save_images_locally():
        def get(self): return self.context.original_save_images_locally
        def set(self, value): self.context.original_save_images_locally = value
        return property(get, set)


class TestHTMLImageCacher(unittest.TestCase):

    def setUp(self):
        placelesssetup.setUp(self)
        zope.component.provideUtility(cache_manager, interfaces.ICacheManager)
        zope.component.provideUtility(cache_keys, interfaces.ICacheKeys)
        zope.component.provideAdapter(Cacheable)
        setSite(portal)

        stub(url_opener, 'open').with_args('http://external.com/image.png').\
                and_return(StringIO('the image contents'))
        stub(cache_keys.getKey).with_args('http://external.com/image.png').\
                and_return('=the-cache-key')
        stub(cache_keys.getURL).with_args('=the-cache-key').\
                and_return('http://external.com/image.png')

    def tearDown(self):
        placelesssetup.tearDown()
        setSite(None)
        cache_manager._items = {}


def run_with_htmls(htmls):
    def multiple_test(original_test):
        def generate_test_method(provided_html, expected_html):
            def new_test(self):
                self.provided_html = provided_html.strip()
                self.expected_html = expected_html.strip()

                context = double(original_html=self.provided_html,
                                 original_save_images_locally=True)

                zope.interface.alsoProvides(
                    context, interfaces.IPossibleHTMLImageCacheable
                )
                self.subject = html_image_cacher.HTMLImageCacher(context)

                if self.on_cache:
                    context.original_save_images_locally = True
                else:
                    context.original_save_images_locally = False

                self.subject.url_opener = url_opener
                self.subject.image_blob_factory = img_blob_factory

                return original_test(self)
            return new_test

        f_locals = inspect.currentframe(1).f_locals
        first_test = None
        for i, (version, (provided_html, expected_html)) in \
                                                    enumerate(htmls.items()):
            new_test = generate_test_method(provided_html, expected_html)
            new_test.__name__ = original_test.__name__ + '_with_' + version
            if i == 0:
                first_test = new_test
            else:
                f_locals[new_test.__name__] = new_test

        return first_test
    return multiple_test

HTMLS = dict(
    img_tag=(
        u"""<html><body>
        <p><img src="http://external.com/image.png" /></p>
        <p><img src="http://internal.com/image.png" /></p>
        </body></html>""",
        u"""<html><body>
        <p><img src="http://internal.com/++tn_plonehtmlimagecache++cache/%3Dthe-cache-key" /></p>
        <p><img src="http://internal.com/image.png" /></p>
        </body></html>""",
    ),
    style_tag=(
        u"""<html><head>
        <style>body{background-image:url('http://external.com/image.png');}</style>
        <style>body{background-image:url('http://internal.com/image.png');}</style>
        </head><body></body>
        </html>""",
        u"""<html><head>
        <style>body{background-image:url('http://internal.com/++tn_plonehtmlimagecache++cache/%3Dthe-cache-key');}</style>
        <style>body{background-image:url('http://internal.com/image.png');}</style>
        </head><body></body>
        </html>""",
    ),
    inline_style=(
        u"""<html><body>
        <p style="background-image:url('http://external.com/image.png');"></p>
        <p style="background-image:url('http://internal.com/image.png');"></p>
        </body></html>""",
        u"""<html><body>
        <p style="background-image:url('http://internal.com/++tn_plonehtmlimagecache++cache/%3Dthe-cache-key');"></p>
        <p style="background-image:url('http://internal.com/image.png');"></p>
        </body></html>""",
    ),
    anchor_tag=(
        u"""<html><body>
        <p><a href="http://external.com/image.png" /></p>
        <p><a href="http://internal.com/image.png" /></p>
        </body></html>""",
        u"""<html><body>
        <p><a href="http://internal.com/++tn_plonehtmlimagecache++cache/%3Dthe-cache-key" /></p>
        <p><a href="http://internal.com/image.png" /></p>
        </body></html>""",
    ),
)

REVERSED_HTMLS = {}
for version, (provided, expected) in HTMLS.items():
    REVERSED_HTMLS[version] = (expected, provided)


@assert_expectations
class TestCacheImages(TestHTMLImageCacher):

    def setUp(self):
        super(TestCacheImages, self).setUp()
        self.on_cache = True

    @run_with_htmls(HTMLS)
    def test_replace_links(self):
        self.subject.update()

        replaced_html = lxml.html.fromstring(self.subject.context.original_html)
        self.assertEquals(
            lxml.html.tostring(lxml.html.fromstring(self.expected_html),
                               pretty_print=True),
            lxml.html.tostring(replaced_html, pretty_print=True)
        )

    @run_with_htmls(HTMLS)
    def test_always_clears_cache_for_context_before_everything(self):
        expect(cache_manager.removeAll).with_args(self.subject.context)
        self.subject.update()

    @run_with_htmls(HTMLS)
    def test_adds_external_image_contents_to_cache(self):
        self.subject.update()
        cached_blob = cache_manager._items[self.subject.context]['=the-cache-key']
        self.assertEquals(cached_blob.s, 'the image contents')

    @run_with_htmls(HTMLS)
    def test_sets_the_correct_filename_in_cached_image(self):
        self.subject.update()
        cached_blob = cache_manager._items[self.subject.context]['=the-cache-key']
        self.assertEquals(cached_blob.filename, 'image.png')

    @run_with_htmls(HTMLS)
    def test_filename_is_a_unicode_string(self):
        self.subject.update()
        cached_blob = cache_manager._items[self.subject.context]['=the-cache-key']
        self.assertTrue(isinstance(cached_blob.filename, unicode))

    @run_with_htmls(HTMLS)
    def test_keeps_links_if_cant_download(self):
        stub(url_opener, 'open').\
                with_args('http://external.com/image.png').\
                and_raise(urllib2.HTTPError,
                          'http://external.com/image.png',
                          666,
                          'an error occurred',
                          {},
                          None)

        self.subject.update()

        replaced_html = lxml.html.fromstring(self.subject.context.original_html)
        self.assertEquals(
            lxml.html.tostring(lxml.html.fromstring(self.provided_html),
                               pretty_print=True),
            lxml.html.tostring(replaced_html, pretty_print=True)
        )


@assert_expectations
class TestRestoreImages(TestHTMLImageCacher):

    def setUp(self):
        super(TestRestoreImages, self).setUp()
        self.on_cache = False

    @run_with_htmls(REVERSED_HTMLS)
    def test_replace_links(self):
        self.subject.update()

        replaced_html = lxml.html.fromstring(self.subject.context.original_html)
        self.assertEquals(
            lxml.html.tostring(lxml.html.fromstring(self.expected_html),
                               pretty_print=True),
            lxml.html.tostring(replaced_html, pretty_print=True)
        )


@assert_expectations
class TestCachedItemSubscriberHandler(unittest.TestCase):

    def setUp(self):
        placelesssetup.setUp(self)
        self.cache_manager = double()
        zope.component.provideUtility(self.cache_manager,
                                      interfaces.ICacheManager)

    def tearDown(self):
        placelesssetup.tearDown()

    def test_remove_all_is_called(self):
        content = object()
        expect(self.cache_manager, 'removeAll').with_args(content)

        html_image_cacher.removeItemsFromCache(content, 'event')
