"""
Test cases built around StoreSite-based classes.

The bulk of the basic tests are handled in TestSite.  More specific cases are
handled in other child classes here.  This module is searched with unittest for
test discovery.  See util.main for that part.
"""

import unittest
from selenium.webdriver.common.keys import Keys
from .store_site import StoreSite
from .test_site_products import TestSiteProducts
from .test_site_collections import TestSiteCollections
from .test_site_mailinglist import TestSiteMailingList

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
        self.check_layout_and_parts()
        self.check_snippet_collection()

    @unittest.skip("not yet implemented")
    def test_template_gift_card(self):
        """Cart should show items and allow checkout"""

    def test_template_index(self):
        """Index page should show a collection"""
        self.get()
        self.check_layout_and_parts()
        self.check_snippet_collection()

    def test_template_list_collections(self):
        """Collections page should show a few products for each collection"""
        self.get("collections")
        self.check_layout_and_parts()
        self.check_for_elem("//article[@class='collections']/section[@class='products']")
        self.check_pagination()

    def test_template_product(self):
        """Product page should show product information"""
        self.get("collections/testing/products/variants")
        if self.is404():
            self.skipTest("testing collection not available")
        self.assertIn("Variants", self.driver.title)
        self.check_layout_and_parts()
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
