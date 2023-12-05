"""
This module defines an implementation of SitemapParser that parses text sitemaps
as returned by the research repository Publisso.
"""

__all__ = []
__version__ = '0.1.0'
__author__ = 'brizuela@ipk-gatersleben.de'

import json

from .sitemap_parser import SitemapParser


BASE_URL = 'https://frl.publisso.de/resource/'


class SitemapParserPublisso(SitemapParser):
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
        frl_ids = [obj["@id"] for obj in json_objs]
        for fid in frl_ids:
            yield f"{BASE_URL}{fid}.json2"


SitemapParserPublisso.register_implementation("publisso")
