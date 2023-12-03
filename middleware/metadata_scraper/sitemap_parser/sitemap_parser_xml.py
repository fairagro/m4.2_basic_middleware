from xml.etree import ElementTree

from .sitemap_parser import SitemapParser


class SitemapParserXml(SitemapParser):

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
        xml_root = ElementTree.fromstring(content)
        for url in xml_root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc' ):
            yield url.text


SitemapParserXml.register_implementation("xml")