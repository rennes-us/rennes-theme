"""
Specific collection scenarios.

See TestSiteCollections for more details.
"""

import re
import unittest
from .store_site import StoreSite
from .util import get_setting

class TestSiteCollections(StoreSite):
    """Test suite for store - collection cases.

    This checks various specific cases for collections pages.  For some of
    these it uses a set of special collections prefixed with "testing," and
    will skip those tests if the collections are not present.  See
    TestSiteProducts for the per-product equivalent.
    """

    def test_template_collection_submenu(self):
        """A collection page for a collection that is with in another category."""
        self.get("collections/skirts")
        self.check_layout()
        self.check_header()
        self.check_instafeed()
        self.check_snippet_address()
        self.check_snippet_mailing_list()
        self.check_nav_site()
        self.check_nav_product(clothing_menu_starts="block")
        self.check_snippet_collection(paginate=False)

    @unittest.skip("not yet implemented")
    def test_template_collection_designers(self):
        """The collection page for the list of designers."""
        self.get("collections/designers")
        self.check_layout()
        self.check_header()
        self.check_instafeed()
        self.check_snippet_address()
        self.check_snippet_mailing_list()
        self.check_nav_site()
        self.check_nav_product()
        self.check_snippet_collection_designers()

    def test_template_collection_empty(self):
        """An empty collection should just show some placeholder text."""
        self.get("collections/testing-empty")
        if self.is404():
            self.skipTest("testing-empty collection not available")
        self.check_layout()
        self.check_header()
        self.check_instafeed()
        self.check_snippet_address()
        self.check_snippet_mailing_list()
        self.check_nav_site()
        self.check_nav_product()
        # Make sure we get the expected text for an empty collection, but
        # disregard whitespace.
        self.assertEqual(
            re.sub(r"\s", "", self.xp("//article[@class='products']").text),
            re.sub(r"\s", "", get_setting("collection_empty_text")))
