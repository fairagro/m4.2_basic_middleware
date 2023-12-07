"""
This module defines an implementation of SitemapParser that parses text sitemaps
as returned by the research repository Publisso.
"""

__all__ = []
__version__ = '0.1.0'
__author__ = 'brizuela@ipk-gatersleben.de, carsten.scharfenberg@zalf.de'


from typing import List

from .sitemap_parser import SitemapParser


class SitemapParserThunenAtlas(SitemapParser):
    """
    An implementation class of SitemapParser that parses text sitemaps as returned by Publisso
    """

    @property
    def has_metadata(self) -> bool:
        """
        A method that returns whether the "sitemap" already contains all needed metadata.

        Returns
        -------
            bool
                Flag indicating whether the "sitemap" already contains all needed metadata.
        """
        return True

    def get_metadata(self) -> List[dict]:
        """
        Return the metadata in case it is already inclued in the sitemap.

        Returns
        -------
            List[dict]
                The metadata in terms of a list of dictionaries.
        """
        return self.parse_content_as_json()['resources']


SitemapParserThunenAtlas.register_implementation("thunen_atlas")
