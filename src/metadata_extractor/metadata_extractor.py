from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import logging
from opentelemetry import trace

class MetadataExtractor(ABC):
    """
    An abstract base class for metadata extractors (aka parsers).
    It will abstract away how the metadata is embedded in a webpage.
    """

    _implementations = {}

    @classmethod
    def _register_implementation(
        cls,
        identifier: str, 
        implementation_class: type["MetadataExtractor"]
    ) -> None:
        """
        Registers an implementation class with a given string identifier so it
        can be created later on by the `create_instance` method.

        Parameters
        ----------
        identifier : str
            The identifier for the implementation.
        implementation_class : type["MetadataExtractor"]
            The class of the implementation.

        Returns
        -------
        None
        """
        cls._implementations[identifier] = implementation_class

    @classmethod
    def create_instance(cls, identifier: str) -> "MetadataExtractor":
        """
        Create an instance of the implementation class based on the identifier.
        
        Parameters
        ----------
            identifier : str
                The identifier of the implementation class.

        Returns
        -------
            MetadataExtractor
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
    def metadata(self, content: str, url: str) -> List[Dict]:
        """
        Extracts metadata from the given content. It is expected that the content can define
        several sets of metadata, so a list is returned.
        Also it is expected that this function will raise Exceptions if something goes wrong,
        e.g. the content is not parsable.

        Arguments
        ---------
            content : str
                The dataset content to extract the metadata from.
            url : str
                The URL to extract metadata from. For some implementations it might be helpful
                to have this information.

        Returns
        -------
            List[Dict]
                A list of dictionaries containing the extracted metadata.
        """
        pass

    @abstractmethod
    def raw_metadata(self, content: str) -> List[str]:
        """
        Extracts unparsed metadata from the given content. It is expected that the content can
        define several sets of metadata, so a list is returned.
        It is expected that this function won't raise exceptions.

        Arguments
        ---------
            content : str
                The dataset content to extract the metadata from.

        Returns
        -------
            List[str]
                A list of strings containing the unprased metadata.
        """
        pass


    def get_metadata_or_log_error(self, content: str, url: str) -> Optional[List[Dict]]:
        """
        Tries to extract metadata from the given content that was downloaded from the given URL.
        If the metadata cannot be extracted, it logs an error and returns None.
        
        Arguments
        ---------
            content : str
                The content to extract metadata from.
            url : str
                The URL associated with the content.
        
        Returns
        -------
            Optional[List[Dict]]
                The extracted metadata if successful, None otherwise.
        """
        with trace.get_tracer(__name__).start_as_current_span("MetadataExtractor.get_metadata_or_log_error") as otel_span:
            try:
                metadata = self.metadata(content, url)
                return metadata
            except Exception as e:
                suspicious_data = ''.join(self.raw_metadata(content))
                otel_span.set_attribute("FAIRagro.middleware.MetadataExtractor.suspicious_data", suspicious_data)
                otel_span.record_exception(e)
                msg = "Could not extract meta data, maybe a parsing error?"
                otel_span.add_event(msg)
                logging.exception(f"{msg}, suspicious data:\n{suspicious_data}")
                return None
