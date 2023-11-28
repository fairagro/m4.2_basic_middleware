from sitemap_parser import SitemapParser
import requests
from w3lib.html import get_base_url
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import json

BASE_URL = 'https://www.openagrar.de/receive/'


class SitemapParserOpenAgrar(SitemapParser):

    def __init__(self, content: str) -> None:
        """
        Initializes an instance of a sitemap parser for XML sitemaps that conform to https://www.sitemaps.org/protocol.html.

        Parameters
        ----------
            content: str
                The content of the "base URL"
        """
        self._content = content
        super().__init__()

    def datasets(self) -> str:
        """
        A asynchronous generator method that returns the URLs to all datasets of the repository.

        Yields
        ------
            str
                A string with the URL to the next dataset.
        """
        json_objs = json.loads(self._content)
        mods_ids = [doc['id'] for doc in json_objs['response']['docs']]
        for mid in mods_ids:
            yield f"{BASE_URL}{mid}"
