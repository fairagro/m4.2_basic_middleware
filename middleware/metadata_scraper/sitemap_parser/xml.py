"""
This module defines an implementation of SitemapParser that parses XML sitemaps
that conform to https://sitemaps.org.
"""

__all__ = []
__version__ = '0.1.0'
__author__ = 'carsten.scharfenberg@zalf.de'


from collections.abc import Iterator
from xml.etree import ElementTree

from middleware.metadata_scraper.sitemap_parser import SitemapParser


class SitemapParserXml(SitemapParser):
    """
    An implementation class of SitemapParser that parses XML sitemaps conforming
    to https://sitemaps.org.
    """

    @property
    def datasets(self,) -> Iterator[str]:
        """
        A generator method that returns the URLs to all datasets of the repository.

        Parameters
        ----------
            content : str
                The contents of the sitemap to be parsed.
        
        Yields
        ------
            str
                A string with the URL to the next dataset.
        """
        xml_root = ElementTree.fromstring(self.content)
        for url in xml_root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc' ):
            if url.text is not None:
                yield url.text


SitemapParserXml.register_implementation("xml")
