"""
This module defines an implementation of SitemapParser that parses text sitemaps
as returned by the research repository Publisso.
"""

__all__ = []
__version__ = '0.1.0'
__author__ = 'brizuela@ipk-gatersleben.de, carsten.scharfenberg@zalf.de'

import json
from typing import List

from .sitemap_parser import SitemapParser, SitemapParseError


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
            list(dict)
                The metadata in terms of a list of dictionaries.
        """
        try:
            json_objs = json.loads(self.content)
        except json.JSONDecodeError as e:
            raise SitemapParseError(e) from e
        return json_objs['resources']


SitemapParserThunenAtlas.register_implementation("thunen_atlas")
