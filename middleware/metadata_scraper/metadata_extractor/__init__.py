"""
Metadata scraper package.
Register available implementations of SitemapParser and MetadataExtractor.
"""

from .embedded_jsonld import MetadataExtractorEmbeddedJsonld
from .jsonld import MetadataExtractorJsonld

MetadataExtractorEmbeddedJsonld.register_implementation('embedded_jsonld')
MetadataExtractorJsonld.register_implementation('jsonld')
