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
        """Test product template for a completely out-of-stock product.

        Theres hould be no add-to-cart button and the product metadata should
        reflect availability.
        """
        self.get(TEST_PRODUCTS["out-of-stock"])
        self.assertIsNone(self.try_for_elem("section[@typeof='Product']//button"))
        # TODO check availability
        self.check_product({"num_images": 1})

    def test_template_product_variants(self):
        """Test product template for a product with multiple variants.

        It should notify us if we try to add to cart without selecting one of
        the variants.  When one is selected, it should be styled appropriately.
        """
        self.get(TEST_PRODUCTS["variants"])
        self.check_variant_required()
        # Default situation:
        variants = self.get_variant_details()
        for var in variants.values():
            self.assertFalse(
                has_border(var["label"]),
                "No variant should be circled yet")
        self.assertEqual(len(variants), 2, "There should be two variants")
        small = variants["small"]
        large = variants["large"]
        # First variant selected:
        small["label"].click()
        self.assertTrue(
            has_border(small["label"]),
            "First variant label should have border")
        self.assertFalse(
            has_border(large["label"]),
            "Second variant label should not have border")
        # Second variant selected:
        large["label"].click()
        self.assertFalse(
            has_border(small["label"]),
            "First variant label should not have border")
        self.assertTrue(
            has_border(large["label"]),
            "Second variant label should have border")
        # General product check
        self.check_product({
            "name": "Variants",
            "description_blurb": "This one has variants.",
            "url": "products/variants",
            "mfg": "rennes-dev",
            "price": "50.00",
            "currency": "USD",
            "condition": "NewCondition",
            "num_images": 2})

    def test_template_product_varying_prices(self):
        """Test product template for a product with differently-priced variants.

        It should notify us if we try to add to cart without selecting one of
        the variants.  When one is selected, it should be styled appropriately,
        and the price listed should reflect the selected variant.
        """
        self.get(TEST_PRODUCTS["varying-prices"])
        self.check_variant_required()
        # Default situation:
        variants = self.get_variant_details()
        for var in variants.values():
            self.assertFalse(
                has_border(var["label"]),
                "No variant should be circled yet")
        self.assertEqual(len(variants), 2, "There should be two variants")
        small = variants["small"]
        large = variants["large"]
        self.assertEqual(
            small["price_spec"].text, "50 USD",
            "First variant's price should be shown")
        self.assertEqual(
            large["price_spec"].text, "",
            "Second variant's price should be hidden")
        # First variant selected:
        small["label"].click()
        self.assertEqual(
            small["price_spec"].text, "50 USD",
            "First variant's price should be shown")
        self.assertEqual(
            large["price_spec"].text, "",
            "Second variant's price should be hidden")
        self.assertTrue(
            has_border(small["label"]),
            "First variant label should have border")
        self.assertFalse(
            has_border(large["label"]),
            "Second variant label should not have border")
        # Second variant selected:
        large["label"].click()
        self.assertEqual(
            small["price_spec"].text, "",
            "First variant's price should be hidden")
        self.assertEqual(
            large["price_spec"].text, "100 USD",
            "Second variant's price should be shown")
        self.assertFalse(
            has_border(small["label"]),
            "First variant label should not have border")
        self.assertTrue(
            has_border(large["label"]),
            "Second variant label should have border")
        # General product check
        self.check_product({
            "name": "Varying Prices",
            "description_blurb": "This one has variants and the big one costs more.",
            "url": "products/varying-prices",
            "mfg": "rennes-dev",
            "price": "50.00",
            "currency": "USD",
            "condition": "NewCondition",
            "num_images": 2})

    def test_template_product_out_of_stock_variant(self):
        """Test product template for a product with one variant out of stock.

        The out of stock variant should have its input element disabled and the
        associated label styled appropriately.  The overall product should be
        available still and the usual rules should apply for variant selection,
        for clarity.
        """
        self.get(TEST_PRODUCTS["running-low"])
        # We still require explicitly selecting a variant, even if only one is
        # available
        self.check_variant_required()
        # check that only one of two variants is available
        variants = self.get_variant_details()
        self.assertIn(
            "SoldOut", variants["rough"]["availability"],
            "Variant should be sold out")
        self.assertIn(
            "InStock", variants["smooth"]["availability"],
            "Variant should be in stock")
        # We can't click the sold out one
        variants["rough"]["label"].click()
        self.check_variant_required()
        # The label should be styled correctly
        self.assertIn(
            "line-through",
            variants["rough"]["label"].value_of_css_property("text-decoration"),
            "Out of stock variant should be shown with strikethrough")
        self.assertEqual(
            variants["rough"]["label"].value_of_css_property("color"),
            "rgba(128, 128, 128, 1)",
            "Out of stock variant should be shown in gray")
        # The input should be disabled
        self.assertEqual(
            variants["rough"]["input"].get_attribute("disabled"),
            "true",
            "Out of stock variant should have disabled input element")
        # The in stock one should be selectable as usual
        variants["smooth"]["label"].click()
        self.assertIsNone(
            variants["smooth"]["input"].get_attribute("disabled"),
            "In stock variant should not be disabled")
        # General product check
        self.check_product({
            "name": "Running Low",
            "description_blurb": "We still have one but not the other.",
            "url": "products/running-low",
            "mfg": "rennes-dev",
            "price": "420.00",
            "currency": "USD",
            "condition": "NewCondition",
            "num_images": 2})

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
            "url": "products/now-cheaper",
            "mfg": "rennes-dev",
            "price": "10.00",
            "compare_price_txt": "1,000 USD",
            "currency": "USD",
            "condition": "NewCondition",
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
        self.check_product({
            "name": "Complex Description",
            "description_blurb": "Text without paragraph and link1\nText with paragraph and link2",
            "url": "products/complex-description",
            "mfg": "rennes-dev",
            "price": "0.00",
            "currency": "USD",
            "condition": "NewCondition",
            "num_images": 0})

    def check_variant_required(self):
        """Check that we can't add-to-cart until selecting a variant."""
        button = self.xp("//button[@type='submit']")
        button.click()
        self.check_for_elem("//span[@class='pick-an-option']")

    def get_variant_details(self):
        """Organize variant information from page in dictionary."""
        variant_attrs = {}

        for span in self.xps("//article[@typeof='Product']//form//span[@property='offers']"):
            avail = self.xp("link[@property='availability']", span).get_attribute("href")
            label = self.xp("label", span)
            input_elem = self.xp("input", span)
            key = label.get_attribute("for")
            variant_attrs[key] = {
                "label": label,
                "input": input_elem,
                "id": key,
                "title": label.text,
                "availability": avail}

        #for label in self.xps("//article[@typeof='Product']//form//label"):
        #    key = label.get_attribute("for")
        #    variant_attrs[key] = {"label": label, "id": key, "title": label.text}
        price_specs = self.check_for_elems("//div[@property='priceSpecification']")
        for price_spec in price_specs:
            key = price_spec.get_attribute("data-variant-id")
            variant_attrs[key]["price_spec"] = price_spec
        # Rearrange to key on text labels
        variant_attrs = {x["label"].text: x for x in variant_attrs.values()}
        return variant_attrs


def has_border(elem):
    """Is a border-radius set on the given element?"""
    return elem.value_of_css_property("border-radius") != "0px"
