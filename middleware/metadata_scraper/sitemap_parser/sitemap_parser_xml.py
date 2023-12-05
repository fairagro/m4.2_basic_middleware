"""
This module defines an implementation of SitemapParser that parses XML sitemaps
that conform to https://sitemaps.org.
"""

__all__ = []
__version__ = '0.1.0'
__author__ = 'carsten.scharfenberg@zalf.de'


from xml.etree import ElementTree

from .sitemap_parser import SitemapParser


class SitemapParserXml(SitemapParser):
    """
    An implementation class of SitemapParser that parses XML sitemaps conforming
    to https://sitemaps.org.
    """

    def datasets(self, content: str) -> str:
        """
        A asynchronous generator method that returns the URLs to all datasets of the repository.

        Parameters
        ----------
            content : str
                The contents of the sitemap to be parsed.
        
        Yields
        ------
            str
                A string with the URL to the next dataset.
        """
        xml_root = ElementTree.fromstring(content)
        for url in xml_root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc' ):
            yield url.text


SitemapParserXml.register_implementation("xml")
