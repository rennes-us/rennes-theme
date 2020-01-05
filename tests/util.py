"""
Various configuration and utilities used elsewhere in the package.
"""

import os
import logging
import json
import unittest
import yaml
# https://stackoverflow.com/a/8910326/4499968
from xvfbwrapper import Xvfb

TESTING_CONFIG = {
    "store_password": os.getenv("SHOPIFY_STORE_PASSWORD"),
    "elem_delay": float(os.getenv("SHOPIFY_TEST_DELAY", "0")),
    "real_x11": os.getenv("SHOPIFY_TEST_SHOW") is not None,
    "log_level": int(os.getenv("SHOPIFY_TEST_LOGLEVEL", "30")),
    # Seems like we sometimes get banned temporarily, probably from hammering
    # instagram's server too hard.
    "check_instafeed": os.getenv("SHOPIFY_CHECK_INSTA", "True").title() == "True",
    "page_load_timeout": 90000 # ms?
    }

logging.basicConfig(level=TESTING_CONFIG["log_level"])
LOGGER = logging.getLogger(__name__)

def __log_testing_config():
    for key in TESTING_CONFIG:
        val = TESTING_CONFIG[key]
        if key == "store_password" and val:
            val = "********"
        LOGGER.info("config: %s=%s", key, val)
__log_testing_config()

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

def main():
    """Run unit tests within virtual X display."""
    unittest_main = lambda: unittest.main(module="tests.test_site")
    if TESTING_CONFIG["real_x11"]:
        unittest_main()
    else:
        with Xvfb():
            unittest_main()


class StoreError(Exception):
    """An Exception for store-related errors."""
