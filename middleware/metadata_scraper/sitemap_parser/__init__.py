"""
This package currently only consists of one public module: sitemap_parser
"""

from .sitemap_parser import * # noqa: F403

# We need to also import these submodules as this is required by the registration process
from .sitemap_parser_xml import * # noqa: F403
from .sitemap_parser_openagrar import * # noqa: F403
from .sitemap_parser_publisso import * # noqa: F403
from .sitemap_parser_thunen_atlas import * # noqa: F403
