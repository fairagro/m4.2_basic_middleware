"""
This module define the abtract base class for sitemap parsers.
"""

from abc import abstractmethod

from utils.registering_abc import RegisteringABC


class SitemapParser(RegisteringABC):
    """
    An abstract base class for sitemap parsers.
    It will abstract away the type of sitemap (xml, json, etc.).
    """

    @abstractmethod
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
