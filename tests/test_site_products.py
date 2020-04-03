"""
Specific product scenarios.

See TestSiteProducts for more details.
"""

import unittest
from .store_site import StoreSite
from .util import TEST_PRODUCTS

class TestSiteProducts(StoreSite):
    """Test suite for store - product cases.

    This checks various specific cases for product pages.  It uses a special
    collection, testing, and will skip these tests if that collection is not
    present.  (This way we can eventually use the same test suite to check on
    the production site, if we also tease apart the add-to-cart step and
    anything else that actually messes with the site.)
    """

    @classmethod
    def setUpClass(cls):
        """Set up browser session, but skip unit if collection is missing."""
        super().setUpClass()
        driver = cls.get_driver()
        driver.get(cls.url + "collections/testing")
        if "Page Not Found" in driver.title:
            raise unittest.SkipTest("testing collection not available")

    def test_template_product_out_of_stock(self):
        """Test product template for a completely out-of-stock product."""
        self.get(TEST_PRODUCTS["out-of-stock"])
        self.assertIsNone(self.try_for_elem("section[@typeof='Product']//button"))
        self.check_product({"availability": "SoldOut", "num_images": 1})

    def test_template_product_variants(self):
        """Test product template for a product with multiple variants.

        It should notify us if we try to add to cart without selecting one of
        the variants.  When one is selected, it should be styled appropriately.
        """
        self.get(TEST_PRODUCTS["variants"])
        self.skipTest("not yet implemented")

    def test_template_product_varying_prices(self):
        """Test product template for a product with differently-priced variants.

        It should notify us if we try to add to cart without selecting one of
        the variants.  When one is selected, it should be styled appropriately.
        """
        self.get(TEST_PRODUCTS["varying-prices"])
        self.skipTest("not yet implemented")

    def test_template_product_out_of_stock_variant(self):
        """Test product template for a product with one variant out of stock."""
        self.get(TEST_PRODUCTS["running-low"])
        # check that only one of two variants is available
        self.skipTest("not yet implemented")

    def test_template_product_lots_of_photos(self):
        """Test product template for a product with a lot of photos.

        These get tricky to display sensibly and flexibly while trying to keep
        the flex CSS working right.
        """
        self.get(TEST_PRODUCTS["lots-of-photos"])
        # check whatever should be checked for when we have a ton of
        # photos.  Make sure the width/height of the thumbnails makes sense,
        # maybe?
        self.skipTest("not yet implemented")

    def test_template_product_on_sale(self):
        """Test product template for a product whose price was lowered.

        For this case there should be a strikethrough version of the original
        price alongside the current price, and an additional disclaimer at the
        bottom of the product details container.
        """
        self.get(TEST_PRODUCTS["now-cheaper"])
        self.check_product({
            "name": "Now Cheaper",
            "description_blurb": "It used to cost more, but now, it costs less!!",
            "url": "collections/testing/products/now-cheaper",
            "mfg": "rennes-dev",
            "price": "10.00",
            "compare_price_txt": "1,000 USD",
            "currency": "USD",
            "condition": "NewCondition",
            "availability": "InStock",
            "num_images": 1})

    def test_template_product_complex_description(self):
        """Test product template for a product with weird description content.

        Since the descriptions can be filled in with the WYSIWYG editor they
        can have all sorts of formatting weirdness in them, and styling them
        consistently is a bit of a pain.  We'll check some basic things here.
        This might not be best organized as a single test but it'll do for now.
        """
        # Links here count as "in text" rather than menu links or what have you
        # so they should always be underlined.
        self.get(TEST_PRODUCTS["complex-description"])
        proddesc = self.check_for_elem(
            "//article[@typeof='Product']/div/div[@property='description']")
        link1 = self.check_for_elem("a", proddesc)
        self.check_decoration_on_hover(link1, "underline", "underline")
        link2 = self.check_for_elem("p/a", proddesc)
        self.check_decoration_on_hover(link2, "underline", "underline")
