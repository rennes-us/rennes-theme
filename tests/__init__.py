"""
Test suite for a browser interacting with the development site.

This ensures that the development site running on Shopify behaves as expected,
referencing the config/settings_data.json here (and assuming that is the same
as Shopify's copy).  I'm working on making this flexible enough to test against
the live theme too, but it's not quite ready yet.  I'd like to let it test the
alternate testing theme too but I can't see an easy way to do that without
having the browser authenticate as a site admin.

This package uses Selenium to automate a locally-running web browser (currently
hardcoded as Chrome).  If the store is password-protected, the environment
variable SHOPIFY_STORE_PASSWORD will be used to supply the store password to
the site.  See the util module for configuration-handling, test_site for the
actual test case classes, and store_site and store_client for high and low
level site interfaces without yet defining the tests themselves.
"""
