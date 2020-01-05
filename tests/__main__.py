"""
Command-line interface for unit testing.

This just exists so that python -m on the package will run the unittest
module's command-line interface.  For more info:
https://docs.python.org/3/library/__main__.html
util.main uses unittest's test discovery to load the test cases it finds in
test_site.  See the classes there for the tests.
"""
from .util import main
main()
