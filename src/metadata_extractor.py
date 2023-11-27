from abc import ABC, abstractmethod
from typing import Dict, List


class MetadataExtractor(ABC):

    @abstractmethod
    def metadata(self, content: str, url: str) -> List[Dict]:
        """
        Extracts metadata from the given URL.

        Arguments
        ---------
            content : str
                The dataset content to extract the metadata from.
            url : str
                The URL to extract metadata from.

        Returns
        -------
            List[Dict]
                A list of dictionaries containing the extracted metadata.
        """
        pass

    @abstractmethod
    def raw_metadata(self, content: str) -> List[str]:
        """
        Extracts a list of unparsed metadata. This may be useful for debugging in case
        the parsing failed.

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
