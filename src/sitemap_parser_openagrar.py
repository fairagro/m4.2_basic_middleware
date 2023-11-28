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
        mods_ids_list = self.mods_id_extractor()
        for mid in mods_ids_list:
            yield f"{BASE_URL}+{mid}"

    def mods_id_extractor(self):
        sitemap_url = 'https://www.openagrar.de/servlets/solr/select?core=main&q=category.top%3A%22mir_genres%3Aresearch_data%22+AND+objectType%3Amods+AND+category.top%3A%22state%3Apublished%22&rows=300&fl=id%2Cmods.identifier&wt=json&XSL.Style=xml'
        response = requests.get(sitemap_url)
        response_json = json.loads(response.text)
        mods_ids = [doc['id'] for doc in response_json['response']['docs']]
        return mods_ids
