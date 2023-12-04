import json

from sitemap_parser import SitemapParser

BASE_URL = "https://frl.publisso.de/resource/"


class SitemapParserPublisso(SitemapParser):
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


SitemapParser._register_implementation("publisso", SitemapParserPublisso)
