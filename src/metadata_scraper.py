from sitemap_parser import SitemapParser
from metadata_extractor import MetadataExtractor


class MetadataScraper:

    def __init__(self, url: str, parser: SitemapParser, extractor: MetadataExtractor) -> None:
        """
        Initialize a MetadataScraper object.

        Parameters
        ----------
        url : str
            The URL of the website to scrape metadata from.
        parser : SitemapParser
            An instance of the SitemapParser class used to parse sitemaps.
        extractor : MetadataExtractor
            An instance of the MetadataExtractor class used to extract metadata.

        Returns
        -------
        None
        """
        self._url = url
        self._parser = parser
        self._extractor = extractor
