"""
Low-level handling of development store site using Selenium.

See the StoreClient class for the main part.
"""

import time
import logging
import unittest

# https://selenium-python.readthedocs.io/getting-started.html
from selenium.webdriver import (Chrome, ChromeOptions)
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException)

from .util import TESTING_CONFIG

LOGGER = logging.getLogger(__name__)


class StoreError(Exception):
    """An Exception for store-related errors."""


class StoreClient(unittest.TestCase):
    """Low-level handling for queries to development store website with Selenium.

    Instances of this class share a single browser session.  Child classes each
    receive their own browser session.  (This is primarily to make
    cache-handling more manageable with unit testing, since a separate test
    case instance is created for each test but it bogs things down too much to
    let each instance start with an empty cache.)
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
        cls.url = "https://" + TESTING_CONFIG["store_site"] + "/"
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
                if "Please Log In" in driver.title:
                    LOGGER.info("Setting up StoreSite: %s: password not accepted", str(cls))
                    raise StoreError("login failed")
            else:
                raise StoreError("No password found in environment variable SHOPIFY_STORE_PASSWORD")

    @classmethod
    def tear_down_site(cls):
        """Clean up after client."""
        LOGGER.info("Cleaning up StoreSite: %s", str(cls))
        # The close method just closes the window.  quit actually quits the
        # browser.  (Possibly I could just del the object, not sure.)
        cls.get_driver().quit()
        del cls.clientmap[cls]

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
            # Why did this start being necessary?  Is our Xvfb still working?
            # https://stackoverflow.com/questions/50642308
            options = ChromeOptions()
            options.add_argument("--headless")
            client = Chrome(options = options)
            client.set_page_load_timeout(TESTING_CONFIG["page_load_timeout"])
            LOGGER.info("No driver for class %s, initialized %s", str(cls), str(client))
            cls.clientmap[cls] = client
        return client

    @property
    def driver(self):
        """Selenium driver in use for all instances of this class."""
        return self.__class__.get_driver()

    @staticmethod
    def click(elem, tries=5, delta=0.1, checker=None):
        """Click an element and make sure it does a thing.

        By default the thing is assumed to be going to a new page, which is
        checked by checking for the staleness of the element.  If the checker
        argument is given, it will instead repeatedly call that until True.  It
        will only try up to tries times, waiting delta seconds between each
        try.

        Background: Selenium's clicking is driving me crazy.  Sometimes clicks
        on simple anchor elements work, and sometimes they just don't do
        anything, despite the page being loaded, the element displayed and
        enabled, etc.  So here I just keep clicking the given element until
        that same element becomes stale (implying we went somewhere else so the
        click actually worked), with a limit on the number of tries.
        """
        # If I just pull the href out and get the URL, that does work, so this
        # seems like a bug to me.  If I sleep for a few seconds before the
        # click that helps but is hardly reliable.  It also "helps" if I check
        # another element on the page in the intervening time, probably just
        # because there's a slight delay then.
        # Maybe related: https://github.com/SeleniumHQ/selenium/issues/4075
        # If all else fails: self.get(elem.get_attribute("href"))
        # Other methods we can check, though no luck yet:
        #  * is_selected
        #  * is_displayed
        #  * is_enabled
        prefix = "click: " + elem.tag_name + " %s"
        log = lambda msg: LOGGER.info(prefix, msg)
        log("click")
        elem.click()
        while tries:
            if checker:
                if checker():
                    log("check passed")
                    return True
                log("check not yet passed")
                time.sleep(delta)
                elem.click()
                tries -= 1
            else:
                try:
                    elem.is_enabled()
                    log("enabled")
                    time.sleep(delta)
                    elem.click()
                    tries -= 1
                except StaleElementReferenceException:
                    log("stale")
                    return True
        log("tries exhausted")
        return False

    def check_for_elem(self, xpath, elem=None):
        """Get a single element by xpath, failing if not found."""
        elem2 = self.try_for_elem(xpath, elem)
        if not elem2:
            self.fail("element not found: \"%s\"" % xpath)
        return elem2

    def check_for_elems(self, xpath, elems=None):
        """Get a list of elements by xpath, failing if not found."""
        elem = self.try_for_elems(xpath, elems)
        if not elem:
            self.fail("element not found: \"%s\"" % xpath)
        return elem

    def try_for_elem(self, xpath, elem=None):
        """Get a single element by xpath, or None if not found."""
        try:
            return self.xp(xpath, elem)
        except NoSuchElementException:
            return None

    def try_for_elems(self, xpath, elems=None):
        """Get a list of elements by xpath, or None if not found."""
        try:
            return self.xps(xpath, elems)
        except NoSuchElementException:
            return None

    def xp(self, xpath, elem=None):
        """Get a single element by xpath."""
        # pylint: disable=invalid-name
        log = lambda msg: LOGGER.debug("xp: %s", msg)
        time.sleep(TESTING_CONFIG["elem_delay"])
        if elem:
            log("in %s: %s" % (elem.tag_name, xpath))
            # As per the docs,
            #      This will select the first link under this element.
            #      myelement.find_element_by_xpath(".//a")
            #      However, this will select the first link on the page.
            #      myelement.find_element_by_xpath("//a")
            # So we'll make sure we have a leading dot!!
            xpath = self._relative(xpath)
            return elem.find_element_by_xpath(xpath)
        log("in page: %s" % xpath)
        return self.driver.find_element_by_xpath(xpath)

    def xps(self, xpath, elem=None):
        """Get a list of elements by xpath."""
        log = lambda msg: LOGGER.debug("xps: %s", msg)
        time.sleep(TESTING_CONFIG["elem_delay"])
        if elem:
            log("in %s: %s" % (elem.tag_name, xpath))
            xpath = self._relative(xpath)
            return elem.find_elements_by_xpath(xpath)
        log("in page: %s" % xpath)
        return self.driver.find_elements_by_xpath(xpath)

    def get(self, path=""):
        """Get a page"""
        LOGGER.info("get: %s", str(path))
        if path.startswith("http"):
            self.driver.get(path)
        else:
            self.driver.get(self.url + path)

    @staticmethod
    def _relative(xpath):
        """Make xpath relative to current element."""
        if not xpath.startswith("."):
            if not xpath.startswith("/"):
                xpath = "/" + xpath
            xpath = "." + xpath
        return xpath
