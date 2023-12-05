"""
This package currently only consists of one public module: sitemap_parser
"""

from .sitemap_parser import *

# We need to also import these submodules as this is required by the registration process
from .sitemap_parser_xml import *
from .sitemap_parser_openagrar import *
from .sitemap_parser_publisso import *
