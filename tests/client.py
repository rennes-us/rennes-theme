#!/usr/bin/env python3

"""
Test suite for a browser interacting with the development site.

This module uses Selenium to automate a locally-running web browser (currently
hardcoded as Chrome).  If the store is password-protected, the environment
variable SHOPIFY_STORE_PASSWORD will be used to supply the store password to
the site.
"""

import os
import logging
import time
import unittest
import json
import yaml

# https://selenium-python.readthedocs.io/getting-started.html
import selenium.webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException)

# https://stackoverflow.com/a/8910326/4499968
from xvfbwrapper import Xvfb

TESTING_CONFIG = {
    "store_password": os.getenv("SHOPIFY_STORE_PASSWORD"),
    "elem_delay": float(os.getenv("SHOPIFY_TEST_DELAY") or 0),
    "real_x11": os.getenv("SHOPIFY_TEST_SHOW") is not None,
    "log_level": int(os.getenv("SHOPIFY_TEST_LOGLEVEL") or 30)
    }

logging.basicConfig(level=TESTING_CONFIG["log_level"])
LOGGER = logging.getLogger(__name__)

TEST_PRODUCTS = {
    "out-of-stock":   "collections/testing/products/out-of-stock",
    "running-low":    "collections/testing/products/running-low",
    "lots-of-photos": "collections/testing/products/lots-of-photos",
    "now-cheaper":    "collections/testing/products/now-cheaper"}

with open("config.yml") as f_in:
    CONFIG = yaml.safe_load(f_in)

with open("config/settings_data.json") as f_in:
    SETTINGS = json.loads(f_in.read())

def get_setting(key):
    """Get the expected store setting from local JSON."""
    return SETTINGS["presets"][SETTINGS["current"]].get(key)


class HasCSSAttr:
    """Selenium condition to verify that an element has a CSS attribute."""
    # pylint: disable=too-few-public-methods

    def __init__(self, element, attr_name, attr_value):
        self.element = element
        self.attr_name = attr_name
        self.attr_value = attr_value

    def __call__(self, driver):
        if self.attr_value == self.element.value_of_css_property(self.attr_name):
            return self.element
        return False


class ElemsHaveText:
    """Selenium condition to verify that elements have visible text."""
    # pylint: disable=too-few-public-methods

    def __init__(self, elements):
        self.elements = elements

    def __call__(self, driver):
        texts = [el.text for el in self.elements if el.text]
        if len(texts) == len(self.elements):
            return self.elements
        return False


class StoreError(Exception):
    """An Exception for store-related errors."""


class StoreSite(unittest.TestCase):
    """Automated queries to development store website.

    This prepares for the tests themselves but can be used independently of the
    test functions.  Instances of this class share a single browser session.
    Child classes each receive their own browser session.
    """

    @classmethod
    def setUpClass(cls):
        LOGGER.info("Setting up StoreSite: %s", str(cls))
        try:
            cls.set_up_site()
        except StoreError as exc:
            cls.fail(str(exc))

    @classmethod
    def tearDownClass(cls):
        cls.tear_down_site()

    @classmethod
    def set_up_site(cls):
        """Set up client and authenticate with site if needed.

        Call this before interacting with any pages.
        """
        driver = cls.get_driver()
        driver.implicitly_wait(1)
        cls.url = "https://" + CONFIG["development"]["store"] + "/"
        driver.get(cls.url)
        LOGGER.info("Setting up StoreSite: %s: loaded %s", str(cls), cls.url)
        try:
            elem = driver.find_element_by_xpath("//input[@type='password']")
        except NoSuchElementException:
            pass
        else:
            LOGGER.info("Setting up StoreSite: %s: reached password prompt", str(cls))
            password = TESTING_CONFIG["store_password"]
            if password:
                elem.send_keys(password)
                elem.send_keys(Keys.RETURN)
                driver.implicitly_wait(1)
                if "Please Log In" in driver.title:
                    LOGGER.info("Setting up StoreSite: %s: password not accepted", str(cls))
                    raise StoreError("login failed")
            else:
                raise StoreError("No password found in environment variable SHOPIFY_STORE_PASSWORD")

    @classmethod
    def tear_down_site(cls):
        """Clean up after client."""
        LOGGER.info("Cleaning up StoreSite: %s", str(cls))
        cls.get_driver().close()

    @classmethod
    def get_driver(cls):
        """Get the Selenium driver object for this class.

        This will transparently manage a dictionary of one driver object for
        all instances of this or any class inheriting from it.  The instances
        of each class share one object distinct from that used by the instances
        of other classes.  These driver objects are initialized as needed when
        they are first referenced via this function.
        """
        clientmap = getattr(cls, "clientmap", None) or {}
        cls.clientmap = clientmap
        try:
            client = cls.clientmap[cls]
        except KeyError:
            client = selenium.webdriver.Chrome()
            LOGGER.info("No driver for class %s, initialized %s", str(cls), str(client))
            cls.clientmap[cls] = client
        return client

    @property
    def driver(self):
        """Selenium driver in use for all instances of this class."""
        return self.__class__.get_driver()

    def add_to_cart(self, product, variant=None):
        """Go to a product page and add it to the cart."""
        self.get("products/" + product)
        if variant:
            for label in self.xps("//form[@typeof='OfferForPurchase']//label"):
                if label.text == variant:
                    label.click()
                    break
        button = self.xp("//form[@typeof='OfferForPurchase']/button[@type='submit']")
        button.click()

    def get_cart_row(self, product_slug, variant_id=None):
        """Get the tr element for a particular product in the cart."""
        url = "/products/" + product_slug
        if variant_id:
            url += "?variant=" + variant_id
        anchor = self.try_for_elem("//form[@action='/cart']//a[@href='" + url + "']")
        if anchor:
            return anchor.find_element_by_xpath("./../..")
        return None

    def check_header(self, bagsize=0):
        """Check the header element (the cart link and such, not <head>)"""
        header = self.xp("/html/body/header")
        cartlink = self.xp(".//a[@href='/cart']", header)
        self.xp(".//form[@action='/search']", header)
        if bagsize > 1:
            self.assertEqual(cartlink.text, bagsize + " items in bag")
        elif bagsize == 1:
            self.assertEqual(cartlink.text, "1 item in bag")
        else:
            self.assertEqual(cartlink.text, "my bag")

    def check_page(self, pagename, pagetitle=None, pageclass="page"):
        """Check one of the free-form pages under /pages/..."""
        self.get("pages/" + pagename)
        self.assertIn(pagetitle or pagename, self.driver.title)
        self.check_for_elem("/html/body/main/article[@class='%s']" % pageclass)
        self.check_instafeed()

    def check_snippet_collection(self, paginate=True):
        """Check a product collection within a page."""
        self.check_for_elem("//article[@class='products']")
        if paginate:
            self.check_for_elem(
                "//article[@class='products']/" +
                "nav[@class='pagination']/span[@class='current']")

    def check_product(self, description_blurb, expected):
        """Check the contents of a single product's page"""
        # Add URL prefix to appropriate attributes
        if "url" in expected:
            expected["url"] = self.url + expected["url"]
        if "condition" in expected:
            expected["condition"] = "http://schema.org/" + expected["condition"]
        if "availability" in expected:
            expected["availability"] = "http://schema.org/" + expected["availability"]
        ### Get basic product structure and metadata
        root = "//article[@typeof='Product']"
        self.check_for_elem(root)
        observed = {}
        prop = lambda t, p: self.check_for_elem((root + "/%s[@property='%s']") % (t, p))
        observed["name"] = prop("h2", "name").text
        observed["url"] = prop("link", "url").get_attribute("href")
        observed["mfg"] = prop("meta", "manufacturer").get_attribute("content")
        ### Get figure and images
        tag = root + "/figure/a[@property='image'][@typeof='ImageObject']"
        self.check_for_elem(tag + "/meta[@property='representativeOfPage'][@content='True']")
        imgset = self.check_for_elem(tag + '/img')
        self.assertEqual(len(imgset.get_attribute("srcset").split(",")), 5)
        self.assertEqual(imgset.get_attribute("property"), "contentUrl")
        if "name" in expected:
            self.assertEqual(imgset.get_attribute("alt"), expected["name"])
        path = root + "/figure/aside/a[@property='image'][@typeof='ImageObject']"
        observed["num_extra_images"] = len(self.check_for_elems(path))
        ### Get cart form and price info
        offer = self.check_for_elem(root + "//form[@property='offers']")
        self.assertEqual(offer.get_attribute("action"), self.url + "cart/add")
        self.assertEqual(offer.get_attribute("method"), "post")
        tag = root + "//form[@property='offers']"
        prop = lambda t, p: self.check_for_elem((tag + "//%s[@property='%s']") % (t, p))
        observed["price"] = prop("span", "price").get_attribute("content")
        observed["currency"] = prop("span", "priceCurrency").get_attribute("content")
        observed["condition"] = prop("link", "itemCondition").get_attribute("href")
        observed["availability"] = prop("link", "availability").get_attribute("href")
        ### Check variants
        # Make sure there's a label and input for each
        # expected variant.
        if "variants" in expected:
            observed["variants"] = {}
            for label in self.check_for_elems(tag + "//label"):
                for inp in self.check_for_elems(tag + "//input[@type='radio']"):
                    if label.get_attribute("for") == inp.get_attribute("id"):
                        observed["variants"][label.text] = label.get_attribute("for")
        ### Get description.
        # This can be a big chunk of HTML so we'll just check that a piece of
        # text is present.
        description = self.check_for_elem(root + "//div[@property='description']").text
        ### Check attributes and description
        for key in expected.keys():
            self.assertEqual(observed[key], expected[key])
        if description_blurb:
            self.assertIn(description_blurb, description)

    def check_product_image_swap(self, altimg=1):
        """Check that clicking thumbnails switches out the main product image."""
        root = "//article[@typeof='Product']"
        tag = root + "/figure/a[@property='image'][@typeof='ImageObject']"
        img = self.xp(tag + '/img')
        thumbnails = self.xps(
            root + "/figure/aside/a[@property='image'][@typeof='ImageObject']/img")
        src = lambda elem: elem.get_attribute("src")
        srcset = lambda elem: elem.get_attribute("srcset")
        # first off, the first thumbnail should be the main image.
        self.assertEqual(src(thumbnails[0]), src(img))
        self.assertEqual(srcset(thumbnails[0]), srcset(img))
        # if we click a different one, that should become the main image.
        self.xp("..", thumbnails[altimg]).click()
        img = self.xp(tag + '/img')
        self.assertEqual(src(thumbnails[altimg]), src(img))
        self.assertEqual(srcset(thumbnails[altimg]), srcset(img))

    def check_nav_site(self):
        """Check the nav element for site links."""
        anchors = self.xps("//nav[@class='main site-nav']/ul/li/a")
        links = [
            ("about", self.url + "pages/about"),
            ("events", self.url + "pages/events"),
            ("news", "http://blog.rennes.us"),
            ("instagram", "https://www.instagram.com/" + get_setting("instagram_handle")),
            ("pinterest", "https://www.pinterest.com/rennes"),
            ("contact", self.url + "pages/contact-us"),
            ("policies", self.url + "pages/policies"),
            ("shipping", self.url + "pages/shipping"),
            ("faq", self.url + "pages/faq")]
        for pair in zip(anchors, links):
            expected = pair[1]
            observed = ((pair[0].text), pair[0].get_attribute("href").strip("/"))
            self.assertEqual(observed, expected)

    def check_nav_product(self, clothing_menu_starts="none"):
        """Check the nav element for product collection links."""
        # Check links and targets
        col = self.url + "collections/"
        links = [
            ("new", col + "new"),
            ("gifts", col + "gifts"),
            ("leather goods", col + "leather-goods"),
            ("clothing", col + "clothing"),
            ("designers", col + "designers"),
            ("home goods", col + "home-goods"),
            ("shoes", col + "shoes"),
            ("sale", col + "sale")]
        self._check_menu_links("//nav[@class='main product-nav']/ul/li/a", links)
        # Check behavior of nested menus
        self._check_menu_collapse("//nav//a[@href='/collections/clothing']", clothing_menu_starts)
        # Check clothing sub-menu
        links = [
            ("tops", col + "tops"),
            ("dresses", col + "dresses"),
            ("pants", col + "pants"),
            ("skirts", col + "skirts"),
            ("sweaters", col + "sweaters"),
            ("coats", col + "coats"),
            ("neck", col + "neck"),
            ("for your hair", col + "for-your-hair"),
            ("bits and bobs", col + "bits-and-bobs")]
        # We need to click the link to expand the menu, or else the .text
        # values on the elements will be blank (because of their invisibility?
        # Not sure but it does make sense for a realistic test.)
        self.xp("//nav//a[@href='/collections/clothing']").click()
        # It can take a moment for the visibility to take effect
        condition = ElemsHaveText(self.xps("//nav//a[@href='/collections/clothing']/../ul/li/a"))
        WebDriverWait(self.driver, 2).until(condition)
        self._check_menu_links("//nav//a[@href='/collections/clothing']/../ul/li/a", links)

    def _check_menu_links(self, xpath, links):
        """Helper for checking nav links."""
        anchors = self.xps(xpath)
        for pair in zip(anchors, links):
            expected = pair[1]
            observed = ((pair[0].text), pair[0].get_attribute("href"))
            self.assertEqual(observed, expected)

    def _check_menu_collapse(self, xpath, starts="none"):
        """Helper for checking collapsing menus within nav elements."""
        menu_link = self.xp(xpath)
        menu_list = self.xp(xpath + "/../ul")
        if starts == "none":
            # Menu starts collapsed
            self.assertEqual(menu_list.value_of_css_property("display"), "none")
            # On click, menu expands
            menu_link.click()
            condition = HasCSSAttr(menu_list, "display", "block")
        else:
            condition = HasCSSAttr(menu_list, "display", starts)
        try:
            WebDriverWait(self.driver, 2).until(condition)
        except TimeoutException:
            self.fail("menu expand failed")
        # On another click, menu collapses
        menu_link.click()
        condition = HasCSSAttr(menu_list, "display", "none")
        try:
            WebDriverWait(self.driver, 2).until(condition)
        except TimeoutException:
            self.fail("menu collapse failed")

    def check_instafeed(self):
        """Check for the instafeed images AJAXd from instagram."""
        elems = self.xps("//section[@id='instafeed']//img")
        self.assertEqual(len(elems), get_setting("instafeed_limit"))

    # TODO check the address chunk at the bottom of most pages.
    def check_snippet_address(self):
        """Check the physical address blurb."""
        #self.check_for_elem("//section[]")

    # TODO check the mailing list chunk at the bottom of most pages.
    def check_mailing_list(self):
        """Check the mailing list signup blurb."""

    def check_snippet_searchresults(self, h2text="Search"):
        """Check the search results snippet."""
        self.check_for_elem("//article[@typeof='SearchResultsPage']")
        el_h2 = self.check_for_elem("//article[@typeof='SearchResultsPage']/h2")
        self.assertEqual(el_h2.text, h2text)
        self.check_snippet_searchform()

    def check_snippet_searchform(self):
        """Check the search form snippet."""
        root = "//article[@typeof='SearchResultsPage']"
        self.check_for_elem(root + "/form[@action='/search'][@role='search']")

    def check_for_elem(self, xpath, elem=None):
        """ Get a single element by xpath, failing if not found."""
        elem = self.try_for_elem(xpath, elem)
        if not elem:
            self.fail("element not found: \"%s\"" % xpath)
        return elem

    def check_for_elems(self, xpath, elems=None):
        """ Get a list of elements by xpath, failing if not found."""
        elem = self.try_for_elems(xpath, elems)
        if not elem:
            self.fail("element not found: \"%s\"" % xpath)
        return elem

    def try_for_elem(self, xpath, elem=None):
        """ Get a single element by xpath, or None if not found."""
        try:
            return self.xp(xpath, elem)
        except NoSuchElementException:
            return None

    def try_for_elems(self, xpath, elems=None):
        """ Get a list of elements by xpath, or None if not found."""
        try:
            return self.xps(xpath, elems)
        except NoSuchElementException:
            return None

    def xp(self, xpath, elem=None):
        """ Get a single element by xpath."""
        # pylint: disable=invalid-name
        time.sleep(TESTING_CONFIG["elem_delay"])
        if elem:
            return elem.find_element_by_xpath(xpath)
        return self.driver.find_element_by_xpath(xpath)

    def xps(self, xpath, elem=None):
        """ Get a list of elements by xpath."""
        time.sleep(TESTING_CONFIG["elem_delay"])
        if elem:
            return elem.find_elements_by_xpath(xpath)
        return self.driver.find_elements_by_xpath(xpath)

    def get(self, path=""):
        """Get a page"""
        LOGGER.info("Loading %s", str(path))
        self.driver.get(self.url + path)


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
        """Cart should show items and allow checkout"""
        # TODO test the update cart link.  It shouldn't require you to check
        # off the disclaimer box, just for checkout itself!
        self.get("cart")
        # Basics
        self.check_header()
        self.check_nav_site()
        self.check_nav_product()
        # Specifics
        elem = self.xp("//main")
        self.assertIn("You don’t have any goods in your bag", elem.text)
        # Features
        # This should add one product to the cart page and bring us back there.
        # Clicking the remove link should take it away.
        self.add_to_cart("elsa-esturgie-boudoir-long-cloud-coat-ecru", "40")
        self.check_header(bagsize=1)
        trow = self.get_cart_row("elsa-esturgie-boudoir-long-cloud-coat-ecru", "15391537561635")
        trow.find_element_by_xpath("//a[@title='Remove Item']").click()
        self.check_header(bagsize=0)
        trow = self.get_cart_row("elsa-esturgie-boudoir-long-cloud-coat-ecru", "15391537561635")
        self.assertIsNone(trow)
        # Let's add it back in, and try to check out.
        self.add_to_cart("elsa-esturgie-boudoir-long-cloud-coat-ecru", "40")
        self.check_header(bagsize=1)
        button = self.xp("//button[@title='Checkout']")
        button.click()
        self.driver.implicitly_wait(1)
        # Nope, not yet, need to check the checkbox
        self.assertNotIn("Checkout", self.driver.title)
        checkbox = self.xp("//input[@id='checkout-warning']")
        checkbox.click()
        button.click()
        self.driver.implicitly_wait(1)
        # Now we've reached checkout
        self.assertIn("Checkout", self.driver.title)
        # Remove item from cart (otherwise it'll throw off other tests since
        # we're sharing one browser session!)
        # TODO probably should handle this more generally to make sure
        # failures/exceptions in one test are isolated and the cart is still
        # properly cleared
        self.get("cart")
        trow = self.get_cart_row("elsa-esturgie-boudoir-long-cloud-coat-ecru", "15391537561635")
        trow.find_element_by_xpath("//a[@title='Remove Item']").click()

    def test_template_collection(self):
        """Collection page"""
        self.get("collections/new")
        self.check_header()
        self.check_instafeed()
        self.check_snippet_address()
        self.check_mailing_list()
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
        self.check_mailing_list()
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
        self.check_mailing_list()
        self.check_nav_site()
        self.check_nav_product()
        # TODO check the collection snippet that gets loaded for this case
        # specifically
        #self.check_snippet_collection()

    @unittest.skip("not yet implemented")
    def test_template_gift_card(self):
        """Cart should show items and allow checkout"""

    def test_template_index(self):
        """Index page should show a collection"""
        self.get()
        self.check_header()
        self.check_instafeed()
        self.check_snippet_address()
        self.check_mailing_list()
        self.check_nav_site()
        self.check_nav_product()
        self.check_snippet_collection()

    def test_template_list_collections(self):
        """Collections page should show a few products for each collection"""
        self.get("collections")
        self.check_header()
        #self.check_instafeed()
        self.check_snippet_address()
        self.check_mailing_list()
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
        self.check_mailing_list()
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
        nav = self.xp("//nav[@class='pagination']")
        first_link = self.try_for_elem("a", elem=nav)
        self.assertFalse("previous" in first_link.text)
        first_link.click()
        nav = self.xp("//nav[@class='pagination']")
        first_link = self.try_for_elem("a", elem=nav)
        self.assertTrue("previous" in first_link.text)
        first_link.click()
        nav = self.xp("//nav[@class='pagination']")
        first_link = self.try_for_elem("a", elem=nav)
        self.assertFalse("previous" in first_link.text)


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
        # TODO check that only one of two variants is available
        self.skipTest("not yet implemented")

    def test_template_product_lots_of_photos(self):
        """Test product template for a product with a lot of photos.

        These get tricky to display sensibly and flexibly while trying to keep
        the flex CSS working right.
        """
        self.get(TEST_PRODUCTS["lots-of-photos"])
        # TODO check whatever should be checked for when we have a ton of
        # photos.  Make sure the width/height of the thumbnails makes sense,
        # maybe?
        self.skipTest("not yet implemented")

    def test_template_product_on_sale(self):
        """Test product template for a product whose price was lowered.

        For this case there should be a strikethrough version of the original
        price alongside the current price.
        """
        self.get(TEST_PRODUCTS["now-cheaper"])
        # TODO make sure the original price is shown in strikethrough next to
        # the new price
        # TODO should these show a disclaimer like the "sale" collection?
        # Should this *be* the sale collection?
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

def main():
    """Run unit tests within virtual X display."""
    if TESTING_CONFIG["real_x11"]:
        unittest.main()
    else:
        with Xvfb():
            unittest.main()
if __name__ == "__main__":
    main()
