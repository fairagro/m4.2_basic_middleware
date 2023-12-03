from abc import ABC
from typing import Self


class RegisteringABC(ABC):
    """
    An abstract base class that support registering implementation classes with
    identifier strings. These identifiers can then be used to create instances of
    the corresponding implementation classes.
    Note: inside the file that defines an implementation class the classmethod
    register_implementation need to be called -- outside of the class definition.
    Actually this could be automated by the use of metaclasses, but this would
    introduce a lot of complexity.
    """

    _implementations = {}

    @classmethod
    def register_implementation(cls: Self, identifier: str) -> None:
        """
        Registers an implementation class with a given string identifier so it
        can be created later on by the `create_instance` method.

        Parameters
        ----------
        identifier : str
            The identifier for the implementation.

        Returns
        -------
        None
        """
        RegisteringABC._implementations[identifier] = cls

    @classmethod
    def create_instance(cls: Self, identifier: str) -> Self:
        """
        Create an instance of the implementation class based on the identifier.
        Currently no arguments to the corresponding initialzer are supported
        (although this cloud easily be changed).
        
        Parameters
        ----------
            identifier : str
                The identifier of the implementation class.

        Returns
        -------
            Self
                An instance of the implementation class specified by the identifier.

        Raises
        ------
            ValueError
                If no implementation is registered for the identifier.
        """
        implementation_class = RegisteringABC._implementations.get(identifier)
        if implementation_class:
            return implementation_class()
        else:
            raise ValueError(f"No implementation registered for identifier '{identifier}'")