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
        self.check_layout_and_parts(clothing_menu_starts="block")
        self.check_snippet_collection(paginate=False)

    @unittest.skip("not yet implemented")
    def test_template_collection_designers(self):
        """The collection page for the list of designers."""
        self.get("collections/designers")
        self.check_layout_and_parts()
        self.check_snippet_collection_designers()

    def test_template_collection_empty(self):
        """An empty collection should just show some placeholder text."""
        self.get_maybe("testing-empty")
        self.check_layout_and_parts()
        # Make sure we get the expected text for an empty collection, but
        # disregard whitespace.
        self.assertEqual(
            re.sub(r"\s", "", self.xp("//article[@class='products']").text),
            re.sub(r"\s", "", get_setting("collection_empty_text")))

    def test_template_collection_sale(self):
        """A collection listing items that are on sale.

        These should show the current price below the strikethrough'd original
        price.
        """
        self.get_maybe("testing-sale")
        self.check_layout_and_parts()
        offer = self.check_for_elem(
            "//section[@typeof='Product']/header/p[@typeof='OfferForPurchase']")
        compare_price = self.check_for_elem("./s", offer)
        new_price = self.check_for_elem("./span[@property='schema:price']", offer)
        num = lambda el: float(re.sub(r"[^0-9\.]", "", el.text))
        self.assertTrue(num(compare_price) > num(new_price))

    def get_maybe(self, collection):
        """Get a collection page, or skip the test if not available."""
        self.get("collections/" + collection)
        if self.is404():
            self.skipTest(collection + " collection not available")
