"""
This module defines the class 'MetadataScraper' and th corresponding class
'MetadataScraperConfig'.
"""

import asyncio
import itertools
from typing import Annotated, Dict, List, NamedTuple, Optional
from opentelemetry import trace
from opentelemetry.semconv.trace import SpanAttributes

from http_session import HttpSession, HttpSessionConfig
from .sitemap_parser import SitemapParser
from .metadata_extractor import MetadataExtractor


class MetadataScraperConfig(NamedTuple):
    """
    A simple configuration class for the HttpSession class.
    """

    name: Annotated[str, "The name of the research data repository to scrape"]
    url: Annotated[str, "The sitemap URL of the research data repository to scrape"]
    sitemap: Annotated[str, "The identifier of the sitemap parser to use"]
    metadata: Annotated[str, "The identifier of the metadata extractor to use"]
    # Unfortunately it's not feasible to nest NamedTuple's, so we use a dict here
    # instead of a HttpSessionConfig instance.
    http_client: Annotated[Optional[Dict],
                           "A http session configuration specialized for this repository"] = None


class MetadataScraper:

    def __init__(self, config: MetadataScraperConfig, default_session_config: Dict) -> None:
        """
        Initialize a MetadataScraper object.

        Parameters
        ----------
        config : MetadataScraperConfig
            The config for this scraper object.
        default_session_config : Dict
            In case the scraper config does not specify a http_client config, this one will be used.
            We use a dict here instead of a HttpSessionConfig instance to conform to the way the
            http session config is treated within MetadataScraperConfig.

        Returns
        -------
        None
        """
        self._config = config
        self._parser = SitemapParser.create_instance(config.sitemap)
        self._extractor = MetadataExtractor.create_instance(config.metadata)
        if config.http_client:
            self._http_session_config = HttpSessionConfig(**config.http_client)
        else:
            self._http_session_config = HttpSessionConfig(**default_session_config)

    async def _extract_metadata(self, url : str, session: HttpSession) -> Optional[List[Dict]]:
        """
        Extracts metadata from the specified URL.

        Parameters
        ----------
        url : str
            The URL from which to extract metadata.
        session : HttpSession
            The http session to use to download the URL content.

        Returns
        -------
        Optional[List[Dict]]
            A dictionary containing the extracted metadata.
        """
        with trace.get_tracer(__name__).start_as_current_span("MetadataScraper.extract_metadata") as otel_span:
            otel_span.set_attribute(SpanAttributes.URL_FULL, url)
            content = await session.get_decoded_url(url)
            metadata = self._extractor.get_metadata_or_log_error(content, url)
            return metadata

    async def _extract_many_metadata(self, urls: List[str], session: HttpSession) -> List[Dict]:
        """
        Extracts metadata for multiple URLs asynchronously.

        Parameters
        ----------
            urls : List[str]
                A list of URLs to extract metadata from.
            session : HttpSession
                The http session to use to download the URLs content.

        Returns
        -------
            List[Dict]
                A list of metadata found at the specified URLs.
                Note that the metadata entries to not correspond 1:1 to the URLs. Each URL may include
                several several metadata entries or none (especially in case the metadata extraction failed).
        """
        metadata = await asyncio.gather(*[self._extract_metadata(url, session) for url in urls])
        filtered_metadata = (m for m in metadata if m is not None)
        result = list(itertools.chain.from_iterable(filtered_metadata))
        return result

    async def scrape_repo(self) -> List[Dict]:
        """
        Scrapes the configured repository for metadata.

        Returns
        -------
            List[Dict]
                The extracted metadata in terms of python dictonaries.
        """
        with trace.get_tracer(__name__).start_as_current_span("MetadataScraper.scrape_repo") as otel_span:
            otel_span.set_attribute("FAIRagro.middleware.MetadataScraper.repository_name", self._config.name)
            otel_span.set_attribute("FAIRagro.middleware.MetadataScraper.repository_sitemap_url", self._config.url)
            async with HttpSession(self._http_session_config) as session:
                sitemap = await session.get_decoded_url(self._config.url)
                urls = self._parser.datasets(sitemap)
                metadata = await self._extract_many_metadata(urls, session)
            return metadata
