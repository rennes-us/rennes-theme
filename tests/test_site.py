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
        self.assertIn("Page Not Found", self.driver.title)
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
        self.check_header()
        self.check_nav_site()
        self.check_nav_product()
        # Specifics
        product = "elsa-esturgie-boudoir-long-cloud-coat-ecru"
        prodid = "15391537561635"
        prodvar = "40"
        elem = self.xp("//main")
        self.assertIn("You don’t have any goods in your bag", elem.text)
        # Features

        # This should add one product to the cart page and bring us back there.
        # Clicking the remove link should take it away.
        self.add_to_cart(product, prodvar)
        self.check_header(bagsize=1)
        trow = self.get_cart_row(product, prodid)
        trow.find_element_by_xpath("//a[@title='Remove Item']").click()
        self.check_header(bagsize=0)
        trow = self.get_cart_row(product, prodid)
        self.assertIsNone(trow)

        # Let's add it back in, and try to check out.
        self.add_to_cart(product, prodvar)
        self.check_header(bagsize=1)
        button = self.xp("//button[@title='Checkout']")
        self.assertFalse(self.click(button))
        # Nope, not yet, need to check the checkbox
        self.assertNotIn("Checkout", self.driver.title)
        checkbox = self.xp("//input[@id='checkout-warning']")
        checkbox.click()
        self.assertTrue(self.click(button))
        # Now we've reached checkout
        self.assertIn("Checkout", self.driver.title)

        # Back to the cart page, check one more thing: the update button.
        # Update the quantity field for one row and click the button.  This
        # should remove the item by setting the quantity to zero, rather than
        # just clicking the remove link as above.
        self.get("cart")
        # TODO this should not be necessary!  Only when clicking the Checkout
        # button, not the Update Shopping Bag button.
        checkbox = self.xp("//input[@id='checkout-warning']")
        checkbox.click()
        qty = self.xp("//input", self.get_cart_row(product, prodid))
        qty.send_keys(Keys.BACKSPACE)
        qty.send_keys("0")
        button = self.xp("//button[@title='Update your total']")
        self.assertTrue(self.click(button))
        # At this point we should have nothing in the cart (otherwise it'll
        # throw off other tests since # we're sharing one browser session!)
        # Probably should handle this more generally to make sure
        # failures/exceptions in one test are isolated and the cart is still
        # properly cleared.
        trow = self.get_cart_row(product, prodid)
        self.assertIsNone(trow)
        self.check_header(bagsize=0)

    def test_template_collection(self):
        """Collection page"""
        self.get("collections/new")
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
        self.check_header()
        self.check_instafeed()
        self.check_snippet_address()
        self.check_snippet_mailing_list()
        self.check_nav_site()
        self.check_nav_product(clothing_menu_starts="block")
        self.check_snippet_collection()

    @unittest.skip("not yet implemented")
    def test_template_collection_designers(self):
        """The collection page for the list of designers."""
        self.get("collections/designers")
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
        self.get("collections/new/products/elsa-esturgie-boudoir-long-cloud-coat-ecru")
        self.assertIn("elsa esturgie boudoir long cloud coat ecru", self.driver.title)
        self.check_header()
        self.check_instafeed()
        self.check_snippet_address()
        self.check_snippet_mailing_list()
        self.check_nav_site()
        self.check_nav_product()
        self.check_product(
            description_blurb=\
            "Organic cotton weave with jersey organic" +
            " cotton lining, the softest coziest coat you will ever own!",
            expected={
                "name": "elsa esturgie boudoir long cloud coat ecru",
                "url": "collections/new/products/elsa-esturgie-boudoir-long-cloud-coat-ecru",
                "mfg": "elsa esturgie",
                "price": "725.00",
                "currency": "USD",
                "condition": "NewCondition",
                "availability": "InStock",
                "num_extra_images": 24,
                "variants": {
                    "36": "15391537496099",
                    "38": "15391537528867",
                    "40": "15391537561635"
                    }
                })
        self.check_product_image_swap()

    def test_template_search(self):
        """Test /search"""
        # Basics
        self.get("/search")
        self.assertIn("Search", self.driver.title)
        self.check_header()
        self.check_nav_site()
        self.check_nav_product()
        # Specifics
        self.check_snippet_searchresults()
        xp_form = "//article[@typeof='SearchResultsPage']/form[@role='search']"
        form = self.xp(xp_form)
        # Features
        query = "socks"
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
        query = "socks"
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

    This checks various specific cases for product pages.
    """

    def test_template_product_out_of_stock(self):
        """Test product template for a completely out-of-stock product."""
        self.get(TEST_PRODUCTS["out-of-stock"])
        self.assertIsNone(self.try_for_elem("section[@typeof='Product']//button"))
        self.check_product(None, {"availability": "SoldOut"})

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
        price alongside the current price.
        """
        self.get(TEST_PRODUCTS["now-cheaper"])
        # Make sure the original price is shown in strikethrough next to
        # the new price
        # Should these show a disclaimer like the "sale" collection?  Should
        # this *be* the sale collection?
        self.skipTest("not yet implemented")


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
