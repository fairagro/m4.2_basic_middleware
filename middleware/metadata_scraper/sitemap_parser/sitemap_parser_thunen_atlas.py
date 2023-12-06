"""
This module defines an implementation of SitemapParser that parses text sitemaps
as returned by the research repository Publisso.
"""

__all__ = []
__version__ = '0.1.0'
__author__ = 'brizuela@ipk-gatersleben.de'

import json

from .sitemap_parser import SitemapParser


BASE_URL = 'https://atlas.thuenen.de/api/v2/resources/'


class SitemapParserThunenAtlas(SitemapParser):
    """
    An implementation class of SitemapParser that parses text sitemaps as returned by Publisso
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
        json_objs = json.loads(content)
        ta_ids = [obj['pk'] for obj in json_objs['resources']]
        for taid in ta_ids:
            yield f"{BASE_URL}{taid}"


SitemapParserThunenAtlas.register_implementation("thunen_atlas")
