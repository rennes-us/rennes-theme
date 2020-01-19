"""
A higher-level browser session interface for a store.

See the StoreSite class for the main part.
"""

import logging
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from .store_client import StoreClient
from .util import (TESTING_CONFIG, get_setting)

LOGGER = logging.getLogger(__name__)


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


class StoreSite(StoreClient):
    """Browser session for development store website.

    This prepares for the tests themselves but can be used independently of the
    test functions.
    """

    def add_to_cart(self, product, variant=None):
        """Go to a product page and add it to the cart."""
        LOGGER.info("add_to_cart: %s (%s)", product, variant)
        self.get("products/" + product)
        if variant:
            label = None
            for label in self.xps("//form[@typeof='OfferForPurchase']//label"):
                if label.text == variant:
                    break
            option = self.xp("//input[@id='" + label.get_attribute("for") + "']")
            self.click(label, checker=option.is_selected)
        button = self.xp("//form[@typeof='OfferForPurchase']/button[@type='submit']")
        self.click(button)

    def get_cart_row(self, product_slug, variant_id=None):
        """Get the tr element for a particular product in the cart."""
        url = "/products/" + product_slug
        if variant_id:
            url += "?variant=" + variant_id
        anchor = self.try_for_elem("//form[@action='/cart']//a[@href='" + url + "']")
        if anchor:
            return anchor.find_element_by_xpath("./../..")
        return None

    def check_layout(self):
        """Check the overall page layout and metadata."""
        elem = self.xp("//meta[@name='google-site-verification']")
        self.assertEqual(
            elem.get_attribute("content"),
            get_setting("google_site_verification"))

    def check_header(self, bagsize=0):
        """Check the header element (the cart link and such, not <head>)"""
        LOGGER.info("check_header (bagsize: %d)", bagsize)
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
        observed["name"] = prop("/h2", "name").text
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
            ("policies", self.url + "pages/policies"),
            ("shipping", self.url + "pages/shipping"),
            ("faq", self.url + "pages/faq"),
            ("instagram", "https://www.instagram.com/" + get_setting("instagram_handle")),
            ("pinterest", "https://www.pinterest.com/rennes"),
            ("podcast", "https://shoprennes.podbean.com"),
            ("contact", self.url + "pages/contact-us")]
        for pair in zip(anchors, links):
            expected = pair[1]
            observed = ((pair[0].text), pair[0].get_attribute("href").strip("/"))
            self.assertEqual(observed, expected)

    def check_nav_product(self, clothing_menu_starts="none"):
        """Check the nav element for product collection links."""
        # Check links and targets
        col = self.url + "collections/"
        links = [
            ("winter sale", col + "winter-sale"),
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
        if TESTING_CONFIG["check_instafeed"]:
            elems = self.xps("//section[@id='instafeed']//img")
            self.assertEqual(len(elems), get_setting("instafeed_limit"))

    def check_snippet_collection(self, paginate=True):
        """Check a product collection within a page."""
        self.check_for_elem("//article[@class='products']")
        if paginate:
            self.check_for_elem(
                "//article[@class='products']/" +
                "nav[@class='pagination']/span[@class='current']")

    def check_snippet_collection_designers(self):
        """Check the special designers collection snippet."""
        self.check_for_elem("//ul[@class='designers']")

    def check_snippet_address(self):
        """Check the physical address blurb."""
        addr = self.check_for_elem("//section[@typeof='PostalAddress']")
        street_txt = [el.text for el in self.xps("//span[@property='streetAddress']", addr)]
        addr_chunk = lambda p: self.xp("//span[@property='%s']" % p, addr).text
        addr_chunk_exp = lambda p: get_setting(p).lower()
        self.assertEqual(street_txt[0], addr_chunk_exp("addr_name"))
        self.assertEqual(street_txt[1], addr_chunk_exp("addr_street"))
        self.assertEqual(addr_chunk("addressLocality"), addr_chunk_exp("addr_city"))
        self.assertEqual(addr_chunk("addressRegion"), addr_chunk_exp("addr_state"))
        self.assertEqual(addr_chunk("postalCode"), addr_chunk_exp("addr_zip"))

    def check_snippet_mailing_list(self):
        """Check the mailing list signup blurb.

        Currently just verifies that the mailing list container and form
        exist.
        """
        elem = self.check_for_elem("//div[@class='mailing-list']")
        #form_xp = "//form[@action='%s']" % get_setting("mailing_list_form_target")
        form_xp = "//form"
        self.check_for_elem(form_xp, elem)

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
