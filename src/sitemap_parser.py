from abc import ABC, abstractmethod


class SitemapParser(ABC):

    @abstractmethod
    def datasets(self) -> str:
        """
        A asynchronous generator method that returns the URLs to all datasets of the repository.

        Yields
        ------
            str
                A string with the URL to the next dataset.
        """
        pass
