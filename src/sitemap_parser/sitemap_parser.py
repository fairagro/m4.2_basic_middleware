from abc import ABC, abstractmethod
from typing import Type


class SitemapParser(ABC):
    """
    An abstract base class for sitemap parsers.
    It will abstract away the type of sitemap (xml, json, etc.).
    """

    _implementations = {}

    @classmethod
    def _register_implementation(
        cls,
        identifier: str, 
        implementation_class: type["SitemapParser"]
    ) -> None:
        """
        Registers an implementation class with a given string identifier so it
        can be created later on by the `create_instance` method.

        Parameters
        ----------
        identifier : str
            The identifier for the implementation.
        implementation_class : type["SitemapParser"]
            The class of the implementation.

        Returns
        -------
        None
        """
        cls._implementations[identifier] = implementation_class

    @classmethod
    def create_instance(cls, identifier: str) -> "SitemapParser":
        """
        Create an instance of the implementation class based on the identifier.
        
        Parameters
        ----------
            identifier : str
                The identifier of the implementation class.

        Returns
        -------
            SitemapParser
                An instance of the implementation class specified by the identifier.

        Returns
        -------
            ValueError: If no implementation is registered for the identifier.
        """
        implementation_class = cls._implementations.get(identifier)
        if implementation_class:
            return implementation_class()
        else:
            raise ValueError(f"No implementation registered for identifier '{identifier}'")

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
        pass
