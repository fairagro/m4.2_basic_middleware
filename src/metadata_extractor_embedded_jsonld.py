from w3lib.html import get_base_url
from extruct import extract
from typing import Dict, List

from metadata_extractor import MetadataExtractor


class MetadataExtractorEmbeddedJsonld(MetadataExtractor):

    def __init__(self) -> None:
        """
        Initializes an instance of the abstract base class of an RDI repository meta data extractor.

        """
        super().__init__()

    def metadata(self, content: str, url: str) -> List[Dict]:
        """
        Extracts embedded JSON-LD metadata from the given content, the.

        Arguments
        ---------
            content : str
                The dataset content to extract the metadata from.
                In this case it's expcted to be an HTML with embedded JSON-LD.
            url : str
                The URL where the content was downloaded from.

        Returns
        -------
            list(dict)
                A list of dictionaries containing the extracted metadata.
        """
        base_url = get_base_url(content, url)
        metadata = extract(content, base_url=base_url, uniform=True, syntaxes=['json-ld'])
        return metadata['json-ld']