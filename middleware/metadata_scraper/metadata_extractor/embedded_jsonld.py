"""
This module defines the class 'MetadataExtractorEmbeddedJsonld' that implements
'MetadataExtractor'.
"""

__all__ = []
__version__ = '0.1.0'
__author__ = 'carsten.scharfenberg@zalf.de'


from typing import Dict, List
from w3lib.html import get_base_url
from extruct import extract
from bs4 import BeautifulSoup

from .metadata_extractor import MetadataExtractor, MetadataParseError


class MetadataExtractorEmbeddedJsonld(MetadataExtractor):
    """
    An implementation of 'MetadataExtractor' that extracts metadata from JSON-LD embedded into
    HTML.
    """

    def metadata(self, content: str, url: str) -> List[Dict]:
        """
        Extracts embedded JSON-LD metadata from the given HTML content.

        Arguments
        ---------
            content : str
                HTML with embedded JSON-LD.
            url : str
                The URL where the content was downloaded from.

        Returns
        -------
            List[Dict]
                A list of dictionaries containing the extracted metadata.
        """
        base_url = get_base_url(content, url)
        try:
            metadata = extract(content, base_url=base_url,
                               uniform=True, syntaxes=['json-ld'])
        except Exception as e:
            raise MetadataParseError(e) from e
        return metadata['json-ld']

    def raw_metadata(self, content: str) -> List[str]:
        """
        Extracts a list of unparsed JSON-LD content from the HTML. This may be useful for
        debugging in case the parsing failed.

        Arguments
        ---------
            content : str
                HTML with embedded JSON-LD.

        Returns
        -------
            List[str]
                A list of strings containing the unparsed JSON-LD.
        """
        soup = BeautifulSoup(content, 'html.parser')
        json_ld = soup.find_all('script', type='application/ld+json')
        metadata = [js.text for js in json_ld]
        return metadata
