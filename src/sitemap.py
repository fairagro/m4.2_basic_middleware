from sitemap_parser import SitemapParser


class Sitemap:

    def __init__(self, name: str, url: str, parser: SitemapParser) -> None:
        """
        Initializes an instance of the abstract base class of an RDI repository sitemap.

        Parameters
        ----------
            name : str
                The name for the sitemap
            url : str
                The "base URL" that offers a sitemap-like behaviour.
            parser: SitemapParser
                The parser that can understand the sitemap content
        """
        self._name = name
        self._url = url
        self._parser = parser

    @property
    async def sitemap(self) -> str:
        """
        Download the sitemap-like URL

        Returns
        -------
            str
                The sitemap-like content
        """
        return self._content

    @abstractmethod
    async def get_datasets(self) -> str:
        """
        A asynchronous generator method that returns the URLs to all datasets of the repository.

        Yields
        ------
            str
                A string with the URL to the next dataset.
        """
        pass
