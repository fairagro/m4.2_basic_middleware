"""
Sitemap parser package.
Register available implementations of SitemapParser.
"""

from .openagrar import SitemapParserOpenAgrar
from .publisso import SitemapParserPublisso
from .thunen_atlas import SitemapParserThunenAtlas
from .xml import SitemapParserXml

SitemapParserOpenAgrar.register_implementation("openagrar")
SitemapParserPublisso.register_implementation("publisso")
SitemapParserThunenAtlas.register_implementation("thunen_atlas")
SitemapParserXml.register_implementation("xml")
