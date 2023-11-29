from sitemap_parser import SitemapParser
import json

BASE_URL = 'https://www.openagrar.de/receive/'


class SitemapParserOpenAgrar(SitemapParser):

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
        mods_ids = [doc['id'] for doc in json_objs['response']['docs']]
        for mid in mods_ids:
            yield f"{BASE_URL}{mid}"


SitemapParser._register_implementation("openagrar", SitemapParserOpenAgrar)