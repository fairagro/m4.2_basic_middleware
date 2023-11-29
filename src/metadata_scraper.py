import asyncio
import itertools
from typing import Dict, List, Optional
from opentelemetry import trace
from opentelemetry.semconv.trace import SpanAttributes

from http_session import HttpSession
from sitemap_parser import SitemapParser
from metadata_extractor import MetadataExtractor


class MetadataScraper:

    def __init__(
        self,
        session: HttpSession,
        parser: SitemapParser,
        extractor: MetadataExtractor
    ) -> None:
        """
        Initialize a MetadataScraper object.

        Parameters
        ----------
        session : HttpSession
            The HTTP session object used for downloading sitemaps and metadata.
        parser : SitemapParser
            An instance of the SitemapParser class used to parse sitemaps.
        extractor : MetadataExtractor
            An instance of the MetadataExtractor class used to extract metadata.

        Returns
        -------
        None
        """
        self._session = session
        self._parser = parser
        self._extractor = extractor

    async def extract_metadata(self, url : str) -> Optional[List[Dict]]:
        """
        Extracts metadata from the specified URL.

        Parameters
        ----------
        url : str
            The URL from which to extract metadata.

        Returns
        -------
        Optional[List[Dict]]
            A dictionary containing the extracted metadata.
        """
        with trace.get_tracer(__name__).start_as_current_span("MetadataScraper.extract_metadata") as otel_span:
            otel_span.set_attribute(SpanAttributes.URL_FULL, url)
            content = await self._session.get_decoded_url(url)
            metadata = self._extractor.get_metadata_or_log_error(content, url)
            return metadata

    async def extract_many_metadata(self, urls: List[str]) -> List[Dict]:
        """
        Extracts metadata for multiple URLs asynchronously.

        Parameters
        ----------
            urls : List[str]
                A list of URLs to extract metadata from.

        Returns
        -------
            List[Dict]
                A list of metadata found at the specified URLs.
                Note that the metadata entries to not correspond 1:1 to the URLs. Each URL may include
                several several metadata entries or none (especially in case the metadata extraction failed).
        """
        metadata = await asyncio.gather(*[self.extract_metadata(url) for url in urls])
        filtered_metadata = (m for m in metadata if m is not None)
        result = list(itertools.chain.from_iterable(filtered_metadata))
        return result

    async def scrape_repo(self, name: str, sitemap_url: str) -> List[Dict]:
        """
        Scrapes a repository for metadata.

        Parameters
        ----------
            name : str
                The name of the repository.
            sitemap_url : str
                The URL of the repository's sitemap (or another URL we can extract the dataset URLs from).

        Returns
        -------
            List[Dict]
                The extracted metadata in terms of python dictonaries.
        """
        with trace.get_tracer(__name__).start_as_current_span("MetadataScraper.scrape_repo") as otel_span:
            otel_span.set_attribute("FAIRagro.middleware.MetadataScraper.repository_name", name)
            otel_span.set_attribute("FAIRagro.middleware.MetadataScraper.repository_sitemap_url", sitemap_url)
            sitemap = await self._session.get_decoded_url(sitemap_url)
            metadata = await self.extract_many_metadata(self._parser.datasets(sitemap))
            return metadata
