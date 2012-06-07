from stubydoo import double, stub, expect, assert_expectations
from tn.plonehtmlimagecache import caching
from tn.plonehtmlimagecache import interfaces
from zope.app.testing import placelesssetup

import unittest
import urllib
import zope.component
import zope.interface
import zope.publisher


class TestCacheManager(unittest.TestCase):
    """Unit test for CacheManager.
    """

    def setUp(self):
        placelesssetup.setUp(self)
        self.cache = {}
        self.context_keys = double(link=lambda *a:None,
                                   unlink=lambda *a:None,
                                   unlinkContext=lambda *a:None,
                                   __contains__=lambda *a:True)
        zope.component.provideUtility(self.cache, interfaces.ICache)
        zope.component.provideUtility(self.context_keys,
                                      interfaces.IContextKeys)
        self.cache_manager = caching.CacheManager()

    def tearDown(self):
        placelesssetup.tearDown()


@assert_expectations
class TestCacheManagerAdd(TestCacheManager):

    def test_links_key_and_context(self):
        context = object()

        expect(self.context_keys.link).to_be_called.\
                with_args('the key', context)
        self.cache_manager.add('the key', context, 'value')

    def test_adds_value_to_cache(self):
        value = object()
        context = object()

        self.cache_manager.add('the key', context, value)
        self.assertEqual(self.cache['the key'], value)


@assert_expectations
class TestCacheManagerRemove(TestCacheManager):

    def test_unlinks_key_and_context(self):
        context = object()

        expect(self.context_keys.unlink).to_be_called.\
                with_args('the key', context).once

        self.cache_manager.remove('the key', context)

    def test_keeps_value_in_cache_if_theres_a_link(self):
        context = object()

        self.cache['the key'] = object()
        stub(self.context_keys.__contains__).with_args('the key').\
                and_return(True)

        self.cache_manager.remove('the key', context)
        self.assertTrue('the key' in self.cache)

    def test_removes_value_from_cache_if_no_key_is_left(self):
        context = object()

        self.cache['the key'] = object()
        stub(self.context_keys.__contains__).with_args('the key').\
                and_return(False)

        self.cache_manager.remove('the key', context)
        self.assertTrue('the key' not in self.cache)

    def test_doesnt_raise_error_if_no_key_is_left_and_cache_has_no_key(self):
        context = object()

        stub(self.context_keys.__contains__).with_args('the key').\
                and_return(False)
        try:
            self.cache_manager.remove('the key', context)
        except:
            self.fail('Removal of key failed unexpectedly')


@assert_expectations
class TestCacheManagerRemoveAll(TestCacheManager):

    def setUp(self):
        super(TestCacheManagerRemoveAll, self).setUp()
        self.cache['the key'] = object()
        self.cache['another key'] = object()
        self.cache['yet another key'] = object()

    def test_removes_values_associated_with_context_from_cache(self):
        context = object()
        keys_to_remove = ['the key', 'another key']
        stub(self.context_keys.unlinkContext).with_args(context).\
                and_return(keys_to_remove)

        self.cache_manager.removeAll(context)

        self.assertTrue('the key' not in self.cache)
        self.assertTrue('another key' not in self.cache)

    def test_keeps_values_not_associated_with_context_in_cache(self):
        context = object()
        keys_to_remove = ['the key', 'another key']
        stub(self.context_keys.unlinkContext).with_args(context).\
                and_return(keys_to_remove)

        self.cache_manager.removeAll(context)

        self.assertTrue('yet another key' in self.cache)


@assert_expectations
class TestCacheManagerItemAccessAndContainment(TestCacheManager):

    def test_get_and_set_item(self):
        context = object()
        value = object()
        self.cache_manager.add('the key', context, value)

        self.assertEqual(self.cache_manager['the key'], value)

    def test_getting_invalid_key_raises_key_error(self):
        self.assertRaises(KeyError, lambda: self.cache_manager['the key'])

    def test_item_containment(self):
        context = object()
        value = object()
        self.cache_manager.add('the key', context, value)

        self.assertTrue('the key' in self.cache_manager)
        self.assertTrue('other key' not in self.cache_manager)


@assert_expectations
class TestCacheManagerTraversing(TestCacheManager):

    def setUp(self):
        super(TestCacheManagerTraversing, self).setUp()
        self.cache_manager = {}
        self.cache_traverser = caching.CacheManagerTraverser(
            self.cache_manager, 'request'
        )
        zope.component.provideUtility(caching.CacheKeys(),
                                      interfaces.ICacheKeys)

    def test_traversing_to_a_known_key(self):
        value = object()
        request = double()
        self.cache_manager['the key'] = value

        traversed = self.cache_traverser.publishTraverse(request, 'the key')

        self.assertTrue(traversed is value)

    def test_traversing_to_a_known_key_marks_request_for_publishing(self):
        value = object()
        request = double()
        self.cache_manager['the key'] = value

        self.cache_traverser.publishTraverse(request, 'the key')

        self.assertTrue(interfaces.ICacheRequest.providedBy(request))

    def test_traversing_to_a_unknown_key_redirects(self):
        response = double(redirect=lambda self, url:None)
        request = double(response=response)
        expect(response.redirect).with_args('the original url')

        cache_keys = zope.component.getUtility(interfaces.ICacheKeys)
        stub(cache_keys.getURL).with_args('unknown key').\
                and_return('the original url')

        self.cache_traverser.publishTraverse(request, 'unknown key')

    def test_traversing_to_a_unknown_key_not_convertible_to_url_raises_not_found(self):
        cache_keys = zope.component.getUtility(interfaces.ICacheKeys)
        stub(cache_keys.getURL).with_args('unknown key').and_return(None)

        self.assertRaises(
            zope.publisher.interfaces.NotFound,
            self.cache_traverser.publishTraverse, 'request', 'unknown key'
        )


class TestCacheKeys(unittest.TestCase):

    def setUp(self):
        self.cache_keys = caching.CacheKeys()

    # These tests ensure that keys are suitable for being used as ids of an OFS
    # folder, which may happen in future (currently we use a ZTK folder).

    def test_keys_has_no_slashes(self):
        # OFS forbids '/' due to traversal.
        url = 'http://plone.org/logo.png'
        self.assertTrue('/' not in self.cache_keys.getKey(url))

    def test_keys_has_no_escaped_slashes(self):
        # Zope will unquote the internal URL (which contain the key) when an
        # object is requested from the cache.  Even a quoted slash will confuse
        # it and make it think it is a continuing path for traversal.
        url = 'http://plone.org/logo.png'
        slash = urllib.quote('/', safe='')
        self.assertTrue(slash not in self.cache_keys.getKey(url))

    def test_keys_start_with_a_tilde(self):
        # A key should not start with an underscore or 'aq_' (OFS requirement),
        # and starting with a '~' fits that.
        url = 'http://plone.org/logo.png'
        key = self.cache_keys.getKey(url)

        self.assertTrue(key.startswith('~'))

    def test_keys_have_no_equal_signs(self):
        # OFS forbids '='.
        # We are assuming the key encoding uses padded strings with equal
        # signs.  Also, we are assuming base64.  If so, a sequence with only
        # two chars should end with an '='.
        url = 'aa'
        key = self.cache_keys.getKey(url)
        # Strip the starting '~'.
        key = key[1:]

        self.assertTrue('=' not in key)

    def test_extension_is_kept(self):
        url = 'http://plone.org/logo.png'
        key = self.cache_keys.getKey(url)

        self.assertTrue(key.endswith('.png'))

    def test_no_dot_if_no_extension(self):
        url = 'http://plone.org/logo'
        key = self.cache_keys.getKey(url)

        self.assertTrue(not '.' in key)

    def test_invariance_with_extension(self):
        url = 'http://plone.org/logo.png'
        key = self.cache_keys.getKey(url)

        self.assertEqual(url, self.cache_keys.getURL(key))
        self.assertEqual(key, self.cache_keys.getKey(self.cache_keys.getURL(key)))

    def test_invariance_without_extension(self):
        url = 'http://plone.org/logo'
        key = self.cache_keys.getKey(url)

        self.assertEqual(url, self.cache_keys.getURL(key))
        self.assertEqual(key, self.cache_keys.getKey(self.cache_keys.getURL(key)))
