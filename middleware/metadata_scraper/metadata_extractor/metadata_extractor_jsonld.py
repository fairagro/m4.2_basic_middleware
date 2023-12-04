"""
This module defines the class 'MetadataExtractorJsonld' that implements
'MetadataExtractor'.
"""

import json
from typing import Dict, List

from .metadata_extractor import MetadataExtractor, MetadataParseError


class MetadataExtractorJsonld(MetadataExtractor):
    """
    An implementation of 'MetadataExtractor' that extracts metadata from pure JSON-LD.
    """

    def metadata(self, content: str, url: str) -> List[Dict]:
        """
        Interpret the given content as metaddata in JSON-LD format 

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
        if not content:
            # we treat empty content as an error because to be consistent with the
            # extruct library
            raise MetadataParseError("Empty content")
        try:
            metadata = json.loads(content)
        except json.JSONDecodeError as e:
            raise MetadataParseError(e) from e
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
