from abc import ABC
from typing import Self


class RegisteringABC(ABC):
    """
    An abstract base class for sitemap parsers.
    It will abstract away the type of sitemap (xml, json, etc.).
    """

    _implementations = {}

    @classmethod
    def register_implementation(
        cls: Self,
        identifier: str
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
        RegisteringABC._implementations[identifier] = cls

    @classmethod
    def create_instance(cls, identifier: str) -> Self:
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
        implementation_class = RegisteringABC._implementations.get(identifier)
        if implementation_class:
            return implementation_class()
        else:
            raise ValueError(f"No implementation registered for identifier '{identifier}'")