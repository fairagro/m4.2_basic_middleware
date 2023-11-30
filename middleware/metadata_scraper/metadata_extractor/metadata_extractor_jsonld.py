import json
from typing import Dict, List

from .metadata_extractor import MetadataExtractor


class MetadataExtractorJsonld(MetadataExtractor):

    def metadata(self, content: str, url: str) -> List[Dict]:
        """
        Interpret the given content as metaddata inJSON-LD format 

        Arguments
        ---------
            content : str
                The dataset content to extract the metadata from.
                In this case it's expcted to be an HTML with embedded JSON-LD.
            url : str
                The URL where the content was downloaded from.

        Returns
        -------
            List[Dict]
                A list of dictionaries containing the extracted metadata.
        """
        metadata = json.load(content)
        if not isinstance(metadata, list):
            return [metadata]
        return metadata
    
    def raw_metadata(self, content: str) -> List[str]:
        """
        Just returns the given JSON-LD, wrapped into an array.

        Arguments
        ---------
            content : str
                JSON-LD content

        Returns
        -------
            List[str]
                A one-element array contains the JSON-LD string.
        """
        return [content]


MetadataExtractorJsonld.register_implementation('jsonld')