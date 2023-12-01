from abc import abstractmethod
from typing import Dict, List, Optional
import logging
from opentelemetry import trace

from utils.registering_abc import RegisteringABC


class MetadataParseError(RuntimeError):
    """
    An excpetion of this type will be thrown by implementations of MetadataExtractor
    if the content cannot be parsed.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(f"Failed to parse metadata: {inner_exception}")
        self.inner_exception = inner_exception


class MetadataExtractor(RegisteringABC):
    """
    An abstract base class for metadata extractors (aka parsers).
    It will abstract away how the metadata is embedded in a webpage.
    """

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
