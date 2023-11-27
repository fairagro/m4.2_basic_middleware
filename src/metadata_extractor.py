from abc import ABC, abstractmethod
from typing import Dict, List


class MetadataExtractor(ABC):

    def __init__(self) -> None:
        """
        Initializes an instance of the abstract base class of an RDI repository meta data extractor.

        """
        pass

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
            list(dict)
                A list of dictionaries containing the extracted metadata.
        """
        pass
