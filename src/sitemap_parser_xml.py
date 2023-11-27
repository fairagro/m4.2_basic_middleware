from xml.etree import ElementTree

from sitemap_parser import SitemapParser


class SitemapParserXml(SitemapParser):

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
        xml_root = ElementTree.fromstring(self._content)
        for url in xml_root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc' ):
            yield url.text
