"""
Test suite for a browser interacting with the development site.

This package uses Selenium to automate a locally-running web browser (currently
hardcoded as Chrome).  If the store is password-protected, the environment
variable SHOPIFY_STORE_PASSWORD will be used to supply the store password to
the site.  See the util module for configuration-handling, test_site for the
actual test case classes, and store_site and store_client for high and low
level site interfaces without yet defining the tests themselves.
"""
