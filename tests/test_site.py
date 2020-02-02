"""
Test cases built around StoreSite-based classes.

The bulk of the basic tests are handled in TestSite.  More specific cases are
handled in other child classes here.  This module is searched with unittest for
test discovery.  See util.main for that part.
"""

import logging
import unittest
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from .store_site import StoreSite
from .util import (get_setting, TEST_PRODUCTS)

LOGGER = logging.getLogger(__name__)

class TestSite(StoreSite):
    """Test suite for store.

    This checks the store site's behavior versus the definitions in the tests
    here and what's expected from the local copy of the settings data.
    """

    ### Tests - Templates

    def test_template_404(self):
        """The 404 page should show a message and the search form."""
        self.get("does-not-exist")
        self.check_layout()
        self.assertTrue(self.is404())
        self.check_for_elem("//form[@action='/search']")

    @unittest.skip("not yet implemented")
    def test_template_article(self):
        """Test blog article"""

    @unittest.skip("not yet implemented")
    def test_template_blog(self):
        """Test blog"""

    def test_template_cart(self):
        """Cart should show items and allow checkout.

        We should be able to add items, remove them, modify the quantity, and
        go to checkout.
        """
        self.get("cart")
        # Basics
        self.check_layout()
        self.check_header()
        self.check_nav_site()
        self.check_nav_product()
        # Specifics
        product = "variants"
        prodid = "31622054412323"
        prodvar = "small"
        elem = self.xp("//main")
        self.assertIn("You don’t have any goods in your bag", elem.text)
        # Features
        # First off, make sure we're on a site that has the the testing
        # collection.  Otherwise we'll stop here.
        self.get("collections/testing")
        if self.is404():
            return

        # This should add one product to the cart page and bring us back there.
        # Clicking the remove link should take it away.
        self.add_to_cart(product, prodvar)
        self.check_header(bagsize=1)
        trow = self.get_cart_row(product, prodid)
        self.assertIsNotNone(trow)
        trow.find_element_by_xpath("//a[@title='Remove Item']").click()
        self.check_header(bagsize=0)
        trow = self.get_cart_row(product, prodid)
        self.assertIsNone(trow)

        # Let's add it back in, and try to check out.
        self.add_to_cart(product, prodvar)
        self.check_header(bagsize=1)
        button = self.xp("//button[@title='Checkout']")
        self.assertFalse(
            self.click(button),
            "Checkout button took effect but disclaimer box was unchecked.")
        # Nope, not yet, need to check the checkbox
        self.assertNotIn(
            "Checkout", self.driver.title,
            "Reached checkout page without checking disclaimer box.")
        checkbox = self.xp("//input[@id='checkout-warning']")
        checkbox.click()
        self.assertTrue(self.click(button), "Checkout button didn't take effect.")
        # Now we've reached checkout
        self.assertIn("Checkout", self.driver.title, "Not on checkout page.")

        # Back to the cart page, check one more thing: the update button.
        # Update the quantity field for one row and click the button.  This
        # should remove the item by setting the quantity to zero, rather than
        # just clicking the remove link as above.
        self.get("cart")
        qty = self.xp("//input", self.get_cart_row(product, prodid))
        qty.send_keys(Keys.ARROW_RIGHT)
        qty.send_keys(Keys.BACKSPACE)
        qty.send_keys("0")
        button = self.xp("//button[@title='Update your total']")
        self.assertTrue(self.click(button), "Cart update button didn't take effect.")
        # At this point we should have nothing in the cart (otherwise it'll
        # throw off other tests since # we're sharing one browser session!)
        # Probably should handle this more generally to make sure
        # failures/exceptions in one test are isolated and the cart is still
        # properly cleared.
        trow = self.get_cart_row(product, prodid)
        self.assertIsNone(trow, "Product still found in cart when it should be absent.")
        self.check_header(bagsize=0)

    def test_template_collection(self):
        """Collection page"""
        self.get("collections/new")
        self.check_layout()
        self.check_header()
        self.check_instafeed()
        self.check_snippet_address()
        self.check_snippet_mailing_list()
        self.check_nav_site()
        self.check_nav_product()
        self.check_snippet_collection()
        self.check_pagination()

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

    @unittest.skip("not yet implemented")
    def test_template_gift_card(self):
        """Cart should show items and allow checkout"""

    def test_template_index(self):
        """Index page should show a collection"""
        self.get()
        self.check_layout()
        self.check_header()
        self.check_instafeed()
        self.check_snippet_address()
        self.check_snippet_mailing_list()
        self.check_nav_site()
        self.check_nav_product()
        self.check_snippet_collection()

    def test_template_list_collections(self):
        """Collections page should show a few products for each collection"""
        self.get("collections")
        self.check_layout()
        self.check_header()
        #self.check_instafeed()
        self.check_snippet_address()
        self.check_snippet_mailing_list()
        self.check_nav_site()
        self.check_nav_product()
        self.check_for_elem("//article[@class='collections']/section[@class='products']")
        self.check_pagination()

    def test_template_product(self):
        """Product page should show product information"""
        self.get("collections/testing/products/variants")
        if self.is404():
            self.skipTest("testing collection not available")
        self.assertIn("Variants", self.driver.title)
        self.check_layout()
        self.check_header()
        self.check_instafeed()
        self.check_snippet_address()
        self.check_snippet_mailing_list()
        self.check_nav_site()
        self.check_nav_product()
        self.check_product({
            "name": "Variants",
            "description_blurb": "This one has variants.",
            "url": "collections/testing/products/variants",
            "mfg": "rennes-dev",
            "price": "50.00",
            "currency": "USD",
            "condition": "NewCondition",
            "availability": "InStock",
            "num_images": 2,
            "variants": {
                "small": "31622054412323",
                "large": "31622054445091",
                }
            })

    def test_template_search(self):
        """Test /search"""
        # Basics
        self.get("/search")
        self.assertIn("Search", self.driver.title)
        self.check_layout()
        self.check_header()
        self.check_nav_site()
        self.check_nav_product()
        # Specifics
        self.check_snippet_searchresults()
        xp_form = "//article[@typeof='SearchResultsPage']/form[@role='search']"
        form = self.xp(xp_form)
        # Features
        query = "ichi"
        elem = self.check_for_elem("input[@type='text']", form)
        elem.send_keys(query)
        elem.send_keys(Keys.RETURN)
        form = self.xp(xp_form)
        self.check_snippet_searchresults('searching for "%s"' % query)
        self.check_for_elems("//article[@typeof='SearchResultsPage']/section[@typeof='Product']")
        self.check_pagination()

    ### Tests - Pages

    def test_page_about(self):
        "Test /pages/about"
        self.check_page("about", "About", "columns page")

    def test_page_events(self):
        "Test /pages/events"
        self.check_page("events")

    def test_page_contact(self):
        "Test /pages/contact-us"
        self.check_page("contact-us", "visit us", "contact page")

    def test_page_policies(self):
        "Test /pages/policies"
        self.check_page("policies")

    def test_page_shipping(self):
        "Test /pages/shipping"
        self.check_page("shipping")

    def test_page_faq(self):
        "Test /pages/faq"
        self.check_page("faq")

    ### Tests - Others

    def test_header_search(self):
        """Test search from the page header."""
        # try with a query that works
        header_input = "//header//form[@role='search']/input[@type='text']"
        results = "//article[@typeof='SearchResultsPage']/section[@typeof='Product']"
        elem = self.xp(header_input)
        query = "ichi"
        elem.send_keys(query)
        elem.send_keys(Keys.RETURN)
        self.check_snippet_searchresults('searching for "%s"' % query)
        self.check_for_elems(results)
        self.check_pagination()
        # a query with no results
        self.get()
        elem = self.xp(header_input)
        query = "verylongsearchquerywithnoresults"
        elem.send_keys(query)
        elem.send_keys(Keys.RETURN)
        self.check_snippet_searchresults('searching for "%s"' % query)
        self.assertEqual(self.try_for_elems(results), [])
        msg_observed = self.xp("//article[@typeof='SearchResultsPage']/p").text
        msg_expected = 'Your search for "%s" did not yield any results' % query
        self.assertEqual(msg_observed, msg_expected)
        self.assertIsNone(self.try_for_elem("//nav[@class='pagination']"))

    ### Tests - Helpers


    def check_pagination(self):
        """Check that pagination links work as expected.

        This will verify there's no "previous" link to start with, click the
        first link (which should be for page 2), and then click the previous
        link.  behavior with multiple pagination elements on the page is not
        curently defined.
        """
        log = lambda msg: LOGGER.info("check_pagination: %s", msg)
        nav = self.xp("//nav[@class='pagination']")
        log("try for first link elem")
        first_link = self.try_for_elem("a", elem=nav)
        log("check that previous is NOT in first link text (\"%s\")" % first_link.text)
        self.assertFalse("previous" in first_link.text.lower())
        log("click first link")
        self.click(first_link)
        nav = self.xp("//nav[@class='pagination']")
        log("try for first link elem again")
        first_link = self.try_for_elem("a", elem=nav)
        log("check that previous IS in first link text (\"%s\")" % first_link.text)
        self.assertTrue("previous" in first_link.text.lower())
        log("click first link again")
        self.click(first_link)
        nav = self.xp("//nav[@class='pagination']")
        log("try for first link elem #3")
        first_link = self.try_for_elem("a", elem=nav)
        log("check that previous is NOT in first link text (\"%s\")" % first_link.text)
        self.assertFalse("previous" in first_link.text.lower())


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


class TestSiteMailingList(StoreSite):
    """Test suite for store - mailing list features"""

    def test_mailing_list(self):
        """Mailing list should only pop up on first visit

        This takes a while.
        """
        if not get_setting("mlpopup_enabled"):
            self.skipTest("mailing list pop-up not enabled")
        self.get()
        self.check_ml_popup()
        self.get()
        self.check_ml_popup(False)

    def check_ml_popup(self, should_pop=True):
        """Check the mailing list popup element.

        This takes a while to run, since there's a delay before it appears on
        screen.
        """
        condition = EC.presence_of_element_located((By.CLASS_NAME, "popup"))
        try:
            delay = get_setting("mlpopup_delay")/1000 + 5
            WebDriverWait(self.driver, delay).until(condition)
        except TimeoutException:
            if should_pop:
                self.fail("mailing list popup not found")
        else:
            if not should_pop:
                self.fail("mailing list popup triggered but shouldn't have")
