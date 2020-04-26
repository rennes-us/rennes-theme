"""
Various configuration and utilities used elsewhere in the package.
"""

import os
import logging
import json
import unittest
import base64
import yaml
# https://stackoverflow.com/a/8910326/4499968
from xvfbwrapper import Xvfb

def __load_theme_config():
    try:
        with open("config.yml") as f_in:
            config = yaml.safe_load(f_in)
    except FileNotFoundError:
        txt = os.getenv("SHOPIFY_THEME_CONFIG_DATA")
        if txt is None:
            raise RuntimeError(
                "config.yml not found; "
                "define SHOPIFY_THEME_CONFIG_DATA with "
                "base64-encoded configuration instead.")
        config = yaml.safe_load(base64.b64decode(txt))
    return config

def __load_settings_data():
    try:
        with open("config/settings_data.json") as f_in:
            settings = json.loads(f_in.read())
    except FileNotFoundError:
        txt = os.getenv("SHOPIFY_SETTINGS_DATA")
        if txt is None:
            raise RuntimeError(
                "config/settings_data.json not found; "
                "define SHOPIFY_SETTINGS_DATA with "
                "base64-encoded configuration instead.")
        settings = json.loads(base64.b64decode(txt))
    return settings

def __setup_testing_config(config):
    testing_config = {
        # TODO unify this around the environment variables themekit uses
        "store_site": config.get("development", {}).get("store") or os.getenv("SHOPIFY_STORE"),
        "store_password": os.getenv("SHOPIFY_STORE_PASSWORD"),
        "elem_delay": float(os.getenv("SHOPIFY_TEST_DELAY", "0")),
        "real_x11": os.getenv("SHOPIFY_TEST_SHOW") is not None,
        "log_level": int(os.getenv("SHOPIFY_TEST_LOGLEVEL", "30")),
        # Seems like we sometimes get banned temporarily, probably from hammering
        # instagram's server too hard.
        "check_instafeed": os.getenv("SHOPIFY_CHECK_INSTA", "True").title() == "True",
        "page_load_timeout": 90000 # ms?
        }
    return testing_config

def __log_testing_config():
    for key in TESTING_CONFIG:
        val = TESTING_CONFIG[key]
        if key == "store_password" and val:
            val = "********"
        LOGGER.info("config: %s=%s", key, val)

CONFIG = __load_theme_config()
SETTINGS = __load_settings_data()
TESTING_CONFIG = __setup_testing_config(CONFIG)

logging.basicConfig(level=TESTING_CONFIG["log_level"])
LOGGER = logging.getLogger(__name__)
__log_testing_config()

TEST_PRODUCTS = {
    "out-of-stock":        "collections/testing/products/out-of-stock",
    "running-low":         "collections/testing/products/running-low",
    "lots-of-photos":      "collections/testing/products/lots-of-photos",
    "now-cheaper":         "collections/testing/products/now-cheaper",
    "variants":            "collections/testing/products/variants",
    "varying-prices":      "collections/testing/products/varying-prices",
    "complex-description": "collections/testing/products/complex-description"}


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
