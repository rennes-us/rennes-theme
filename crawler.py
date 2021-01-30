#!/usr/bin/env python
"""
Continuous checker for live site.
"""

import re
import logging
import time
from pathlib import Path
from tests.store_client import StoreClient
from tests.util import TESTING_CONFIG

DELAY = 1

class Crawler(StoreClient):

    def __init__(self):
        super().__init__()
        self.__class__.config = TESTING_CONFIG.copy()
        self.config["store_site"] = "www.rennes.us"
        self.visited = []
        self.depth = 0
        self.logger = self.setup_log()

    def setup_log(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        stream = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)-8s] %(context)s%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S")
        stream.setFormatter(formatter)
        logger.addHandler(stream)

        # https://docs.python.org/3/howto/logging-cookbook.html#logging-cookbook
        crawler = self
        class ContextFilter(logging.Filter):
            def filter(self, record):
                collection = ""
                product = ""
                depth = ""
                if hasattr(crawler, "url"):
                    parts = crawler.parse_path()
                    collection = parts["collection"]
                    product = parts["product"]
                    depth = str(crawler.depth)
                context = [("D:", depth), ("C:", collection), ("P:", product)]
                context = [c[0] + c[1] for c in context if c[1]]
                context = " ".join(context)
                if context:
                    context += " "
                record.context = context
                return True

        logger.addFilter(ContextFilter())
        return logger

    def __del__(self):
        self.tear_down_site()

    def parse_path(self, path=None):
        if not path:
            path = self.path()
        fields = list(path.parts)
        if fields and fields[0] == "/":
            fields.pop(0)
        parts = {"collection": "", "product": ""}
        if len(fields) > 1 and fields[0] == "collections":
            fields.pop(0)
            parts["collection"] = fields.pop(0)
            if len(fields) > 1 and fields[0] == "products":
                fields.pop(0)
                parts["product"] = fields.pop(0)
        elif len(fields) > 1 and fields[0] == "products":
            fields.pop(0)
            parts["product"] = fields.pop(0)
        elif len(fields) > 1 and fields[0] == "pages":
            fields.pop(0)
            parts["page"] = fields.pop(0)
        return parts

    def crawl_main(self):
        self.logger.info("Setup started")
        self.set_up_site(self.config)
        self.logger.info("Setup done")
        self.get("/")
        self.visited.append(self.path())
        self.crawl()
    
    def path(self, url=None):
        if not url:
            url = self.driver.current_url
        prefix = self.url
        if url.startswith(prefix):
            url = url[len(prefix):]
        if not url.startswith("/"):
            url = "/" + url
        return Path(url)

    def get_local_urls(self, elem):
        """Get all local URLs referenced under the given elem."""
        links = self.xps("//a", self.xp(elem))
        urls = [link.get_attribute("href") for link in links]
        urls = [url for url in urls if url.startswith(self.url)]
        return urls

    def crawl(self):
        # crawl breadth-first across pages
        # check where we already are
        self.depth += 1
        checks = {
            Path("/"): self.check_index,
            Path("/collections/designers"): self.check_collection_designers,
            Path("/pages/policies"): self.check_page_policies}
        path = self.path()
        checker = checks.get(path)
        if checker:
            self.logger.debug("Found checker for path %s", path)
            checker()
        else:
            # implicit checks
            parts = self.parse_path()
            if parts["product"]:
                checker = self.check_product
                self.logger.debug("Calling generic product checker for path %s", path)
                checker()
            elif parts["collection"]:
                checker = self.check_collection
                self.logger.debug("Calling generic collection checker for path %s", path)
                checker()
            elif parts["page"]:
                checker = self.check_page
                self.logger.debug("Calling generic page checker for path %s", path)
                checker()
            else:
                self.logger.debug("No checker for path %s", path)
        # then loop over things to check
        # if they're not already in the visited set
        # go there, add them, and call crawl()
        urls = self.get_local_urls("//nav[@class='main product-nav']")
        urls += self.get_local_urls("//nav[@class='main site-nav']")
        # skip any we've already visited
        keep = lambda url: self.path(url) not in self.visited
        urls = [url for url in urls if keep(url)]
        # pre-emptively add to the visited list so that inner calls ignore
        # these
        self.visited += [self.path(url) for url in urls]
        for url in urls:
            self.get(url)
            self.crawl()
        self.depth -= 1

    def get_section_info(self, section):
        return [
            self.xp("header/div[@property='name']", section).text,
            self.xp("a", section).get_attribute("href")]

    def check_index(self):
        sections = self.xps("//article/section")
        infos = [self.get_section_info(sec) for sec in sections]
        self.logger.info("loaded %s product sections", len(infos))
        #for info in infos:
        #    self.get(info[1])
        #    self.logger.info("Checking product page")
        #    self.driver.back()
        #    time.sleep(DELAY)

    def check_collection_designers(self):
        ul_top = self.xp("//ul[@class='designers']")
        # Check the order and formatting of the headings
        headings = [elem.text.split()[0] for elem in self.xps("./li", ul_top)]
        self.logger.debug(headings)
        matches = [re.match(r"^[a-z]\.$", head) for head in headings]
        if all(matches):
            self.logger.info("headings format: OK")
        else:
            self.logger.error("headings format: not all match pattern")
        if headings == sorted(headings):
            self.logger.info("headings order: OK")
        else:
            self.logger.error("headings order: not sorted")
        # TODO confirm that all vendors get a collection and all collections
        # get a link
        items = self.xps("//ul/li", ul_top)

    def check_page_policies(self):
        pass

    def check_product(self):
        self.logger.warning("TODO: check_product")

    def check_collection(self):
        self.logger.warning("TODO: check_collection")

    def check_page(self):
        self.logger.warning("TODO: check_page")


if __name__ == "__main__":
    Crawler().crawl_main()
