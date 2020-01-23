"""
A higher-level browser session interface for a store.

See the StoreSite class for the main part.
"""

import logging
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from .store_client import StoreClient
from .util import (TESTING_CONFIG, get_setting)

LOGGER = logging.getLogger(__name__)

WINDOWSIZES = {
    "small": {"width": 320, "height": 568}, # iPhone SE
    "medium": {"width": 1024, "height": 768}, # old-school computer
    "large": {"width": 3840, "height": 2160} # My ASUS ZenBook
    }

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

    def is404(self):
        """Did we get a 404 on the most recent request?"""
        return "Page Not Found" in self.driver.title

    def add_to_cart(self, product, variant=None):
        """Go to a product page and add it to the cart.

        If variant is given, select that variant.  ValueError is raised if the
        given variant isn't found in the page, or if no variant is given but
        variants are available.
        """
        LOGGER.info("add_to_cart: %s (%s)", product, variant)
        self.get("products/" + product)
        if variant:
            label = None
            for label in self.xps("//form[@typeof='OfferForPurchase']//label"):
                if label.text == variant:
                    break
            else:
                raise ValueError(
                    "product %s: variant \"%s\" not found" % (str(product), str(variant)))
            option = self.xp("//input[@id='" + label.get_attribute("for") + "']")
            self.click(label, checker=option.is_selected)
        else:
            if self.try_for_elems("//form[@typeof='OfferForPurchase']//label"):
                raise ValueError(
                    "product %s: no variant given but variants available")
        button = self.xp("//form[@typeof='OfferForPurchase']/button[@type='submit']")
        self.click(button)
        cartlink = self.xp("//body/header//a[@href='/cart']")
        self.assertNotEqual(cartlink.text, "my bag")

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
        # the main title is a special case, no underline
        h1link = self.xp(".//h1/a", header)
        self.check_decoration_on_hover(h1link, "none ")
        cartlink = self.xp(".//a[@href='/cart']", header)
        self.check_decoration_on_hover(cartlink)
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

    def check_product(self, expected):
        """Check the contents of a single product's page"""
        # Add URL prefix to appropriate attributes
        if "url" in expected:
            expected["url"] = self.url + expected["url"]
        if "condition" in expected:
            expected["condition"] = "http://schema.org/" + expected["condition"]
        if "availability" in expected:
            expected["availability"] = "http://schema.org/" + expected["availability"]
        self.check_for_elem("//article[@typeof='Product']")
        observed = {}
        prop = lambda t, p: self.check_for_elem(
            ("//article[@typeof='Product']/%s[@property='%s']") % (t, p))
        observed["name"] = prop("/h2", "name").text
        observed["url"] = prop("link", "url").get_attribute("href")
        observed["mfg"] = prop("meta", "manufacturer").get_attribute("content")
        self._check_product_figure(observed, expected)
        self._check_product_description(observed, expected)
        self._check_product_offer(observed, expected)
        self._check_product_aside(observed, expected)
        self._check_product_image_zoom()
        self._check_product_image_swap_arrows(expected)
        for key in expected.keys():
            self.assertEqual(observed[key], expected[key])

    def _check_product_figure(self, observed, expected):
        """Check the figure portion of a product page."""
        # Check the figure and main image
        figure = self.check_for_elem("//article[@typeof='Product']/figure")
        anchor = self.check_for_elem("a[@property='image'][@typeof='ImageObject']", figure)
        self.check_for_elem("meta[@property='representativeOfPage'][@content='True']", anchor)
        imgset = self.check_for_elem('img', anchor)
        self.assertEqual(len(imgset.get_attribute("srcset").split(",")), 5)
        self.assertEqual(imgset.get_attribute("property"), "contentUrl")
        if "name" in expected:
            self.assertEqual(imgset.get_attribute("alt"), expected["name"])
        # check the cursor style on the main anchor
        self.assertEqual(
            anchor.value_of_css_property("cursor"),
            "zoom-in")
        # Check the thumbnails
        aside_anchors = self.check_for_elems(
            "aside/a[@property='image'][@typeof='ImageObject']", figure)
        observed["num_images"] = len(aside_anchors)

    def _check_product_offer(self, observed, expected):
        """Check the offer (price and purchase info) portion of a product page."""
        tag = "//article[@typeof='Product']//form[@property='offers']"
        offer = self.check_for_elem(tag)
        self.assertEqual(offer.get_attribute("action"), self.url + "cart/add")
        self.assertEqual(offer.get_attribute("method"), "post")
        prop = lambda t, p: self.check_for_elem((tag + "//%s[@property='%s']") % (t, p))
        if "compare_price_txt" in expected:
            observed["compare_price_txt"] = self.check_for_elem(tag + "//s").text
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
        button = self.check_for_elem("/button[@type='submit']", offer)
        if "/SoldOut" in expected["availability"]:
            self.assertEqual(button.get_attribute("disabled"), "true")
            self.assertEqual(offer.text, "100 USD\nSold Out")
        else:
            # The add to cart button should get a black border on hover, or, on
            # small screens, should always have a black border.
            with self.window_size(WINDOWSIZES["large"]):
                self.check_decoration_on_hover(
                    button, "1px ", "0px ", "border")
            with self.window_size(WINDOWSIZES["small"]):
                self.check_decoration_on_hover(
                    button, "1px ", "1px ", "border")

    def _check_product_aside(self, observed, expected):
        """Check the aside portion of a product page.

        This should always include a blurb linking to contact and policies, and
        for sale pages, a second blurb about final sale.
        """
        # Note that there's another aside, inside the figure.  We don't want
        # that one.
        tag = "//article[@typeof='Product']/div/aside"
        aside = self.check_for_elem(tag)
        smalls = self.check_for_elems("small", aside)
        anchors = self.check_for_elems("a", smalls[0])
        links = [
            ("contact", self.url + "pages/contact"),
            ("policies", self.url + "pages/policies")]
        for pair in zip(anchors, links):
            exp = pair[1]
            obs = ((pair[0].text), pair[0].get_attribute("href"))
            self.assertEqual(obs, exp)
            self.check_decoration_on_hover(pair[0], "underline", "underline")
        numify = lambda txt: float(re.sub("[^0-9.]", "", txt))
        if "compare_price_txt" in expected and \
            numify(expected["compare_price_txt"]) > numify(expected["price"]):
            self.assertEqual(len(smalls), 2)
            self.assertEqual(
                smalls[1].get_attribute("class"),
                "sale-disclaimer")
        else:
            self.assertEqual(len(smalls), 1)

    def _check_product_description(self, observed, expected):
        """Check the description portion of a product page.

        This can be a big chunk of HTML so we'll just check that a piece of
        text is present.
        """
        observed["description"] = self.check_for_elem(
            "//article[@typeof='Product']//div[@property='description']").text
        ### Check attributes and description
        if "description_blurb" in expected:
            self.assertIn(expected["description_blurb"], observed["description"])
            del expected["description_blurb"]

    def _check_product_image_zoom(self):
        """Check that clicking on the main product image zooms/unzooms."""
        figure = self.xp("//article[@typeof='Product']/figure")
        anchor = self.xp("a", figure)
        aside = self.xp("aside", figure)
        # Confirm that as we click on the anchor and then on the zoomed image
        # (in the aside), the class on the aside gets "zoomed" added/removed.
        # Note that we click on the main anchor to do the zoom, but then the
        # aside (since that's what's takng up the whole viewport) to do the
        # un-zoom.
        self.assertEqual(aside.get_attribute("class"), "")
        anchor.click()
        self.assertEqual(aside.get_attribute("class"), "zoomed")
        aside.click()
        self.assertEqual(aside.get_attribute("class"), "")

    def _check_product_image_swap_arrows(self, expected):
        """Check that clicking left/right arrows switches the product image.

        Clicking the left and right links should swap out the images in order.
        Going past the left edge should wrap around to the last image, and
        going past the right edge should wrap around to the first image.
        """
        figure = self.check_for_elem("//article[@typeof='Product']/figure")
        getimg = lambda: self.check_for_elem(
            "/a[@property='image'][@typeof='ImageObject']/img",
            figure)
        checksrc = lambda img: self.assertEqual(
            getimg().get_attribute("src"),
            img.get_attribute("src"))
        figure = self.check_for_elem("//article[@typeof='Product']/figure")
        # Check the left and right links
        left = self.check_for_elem("a[@class='arrow left']", figure)
        right = self.check_for_elem("a[@class='arrow right']", figure)
        self.assertEqual(left.value_of_css_property("cursor"), "pointer")
        self.assertEqual(right.value_of_css_property("cursor"), "pointer")
        self.assertEqual(left.text, get_setting("product_left_image_text"))
        self.assertEqual(right.text, get_setting("product_right_image_text"))
        # Starting off, the first thumbnail should match the main image
        thumbnails = self.check_for_elems(
            "/aside/a[@property='image'][@typeof='ImageObject']/img",
            figure)
        num = expected["num_images"]
        self.assertEqual(len(thumbnails), num)
        checksrc(thumbnails[0])
        # wrap around backwards
        left.click()
        checksrc(thumbnails[num-1])
        # back to beginning
        right.click()
        # click through the rest.  The last click should wrap us around to the
        # first image
        for click in range(num):
            checksrc(thumbnails[click])
            right.click()
        ## wrap around forwards
        checksrc(thumbnails[0])

    def _check_product_image_swap(self, altimg=1):
        """Check that clicking thumbnails switches out the main product image.

        We're not currently using this method; see the arrows method instead.
        """
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
            self.check_decoration_on_hover(pair[0])

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
            self.check_decoration_on_hover(pair[0])

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
        # Check the layout of the product sections.  These should flow smoothly
        # with the CSS flex magic, showing 2, 3, and 4 products per row on
        # small, medium, and large screens respectively.
        sections = self.check_for_elems("//section[@typeof='Product']")
        self.driver.set_window_size(
            WINDOWSIZES["small"]["width"], WINDOWSIZES["small"]["height"])
        self._check_wrap(sections, 2)
        self.driver.set_window_size(
            WINDOWSIZES["medium"]["width"], WINDOWSIZES["medium"]["height"])
        self._check_wrap(sections, 3)
        self.driver.set_window_size(
            WINDOWSIZES["large"]["width"], WINDOWSIZES["large"]["height"])
        self._check_wrap(sections, 4)

    def _check_wrap(self, elems, num):
        """Given a list of elements, check that they wrap as expected.

        This checks the x and y coordinates of the first few items to make sure
        the expected number are on the first row and first column (assuming a
        grid-like layout).
        """
        # Elements 0 to num-1 should be on the same row (same y) while 0 and
        # num should be on the same column (same x)
        self.assertEqual(
            int(elems[0].rect["y"]),
            int(elems[num-1].rect["y"]))
        self.assertEqual(
            int(elems[0].rect["x"]),
            int(elems[num].rect["x"]))

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

    def check_decoration_on_hover(self, elem, value2="underline ", value1="none ",
                                  attr="text-decoration"):
        """Ensure an element's text-decoration (or other CSS) appears on hover."""
        css = lambda: elem.value_of_css_property(attr)
        self.assertTrue(
            css().startswith(value1),
            "expected CSS property %s to start with %s but saw %s" % (attr, value1, css()))
        self.hover(elem)
        self.assertTrue(
            css().startswith(value2),
            "expected CSS property %s to start with %s but saw %s" % (attr, value2, css()))
