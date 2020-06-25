"""
Additional testing for the mailing list features.

This needs to be in a separate TestCase so that it starts with an empty cache
and we can test the one-time popup.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from .store_site import StoreSite
from .util import get_setting

class TestSiteMailingList(StoreSite):
    """Test suite for store - mailing list features"""

    def test_mailing_list_popup(self):
        """Mailing list should only pop up on first visit

        This takes a while.
        """
        if not get_setting("mlpopup_enabled"):
            self.skipTest("mailing list pop-up not enabled")
        self.get()
        self.check_ml_popup()
        self.get()
        self.check_ml_popup(False)

    def test_mailing_list(self):
        self.skipTest("not implemented")
        # TODO
        # check that:
        # * we can't click submit without an email address
        # * once we put one it, it goes to mailchimp

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
