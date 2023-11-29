from w3lib.html import get_base_url
from extruct import extract
from bs4 import BeautifulSoup
from typing import Dict, List

from metadata_extractor import MetadataExtractor


class MetadataExtractorEmbeddedJsonld(MetadataExtractor):

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
        metadata = extract(content, base_url=base_url, uniform=True, syntaxes=['json-ld'])
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
        metadata = [ js.text for js in json_ld ]
        return metadata
    

MetadataExtractor._register_implementation('embedded_jsonld', MetadataExtractorEmbeddedJsonld)