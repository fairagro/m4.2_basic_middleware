"""
This module defines an implementation of SitemapParser that parses text sitemaps
as returned by the research repository OpenAgrar.
"""

__all__ = []
__version__ = '0.1.0'
__author__ = 'brizuela@ipk-gatersleben.de'


import json

from .sitemap_parser import SitemapParser


BASE_URL = 'https://www.openagrar.de/receive/'


class SitemapParserOpenAgrar(SitemapParser):
    """
    An implementation class of SitemapParser that parses text sitemaps as returned by OpenAgrar
    """

    @property
    def datasets(self) -> str:
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
        json_objs = json.loads(self.content)
        mods_ids = [doc['id'] for doc in json_objs['response']['docs']]
        for mid in mods_ids:
            yield f"{BASE_URL}{mid}"


SitemapParserOpenAgrar.register_implementation("openagrar")
