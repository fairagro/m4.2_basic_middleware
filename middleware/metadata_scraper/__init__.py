"""
This module defines the class 'MetadataScraper' and th corresponding class
'MetadataScraperConfig'.
"""

import asyncio
import itertools
import logging
from typing import Annotated, Dict, List, NamedTuple, Optional, Tuple
from opentelemetry import trace
from opentelemetry.semconv.attributes import url_attributes

from middleware.http_session import (
    HttpSession,
    HttpSessionConfig,
    HttpSessionDecodeError,
    HttpSessionFetchError,
    HttpSessionResponseError
)
from middleware.metadata_scraper.sitemap_parser.sitemap_parser import (
    SitemapParseError, SitemapParser)
from middleware.metadata_scraper.metadata_extractor.metadata_extractor import (
    MetadataExtractor, MetadataParseError)
from middleware.utils.tracer import traced


class MetadataScraperConfig(NamedTuple):
    """
    A simple configuration class for the HttpSession class.
    """

    name: Annotated[str, "The name of the research data repository to scrape"]
    url: Annotated[str,
                   "The sitemap URL of the research data repository to scrape"]
    sitemap: Annotated[str, "The identifier of the sitemap parser to use"]
    metadata: Annotated[Optional[str],
                        "The identifier of the metadata extractor to use"] = None
    commit: Annotated[Optional[bool],
                      "If set to false, the harvested metadata will not be committed to git"] = True
    # Unfortunately it's not feasible to nest NamedTuple's, so we use a dict here
    # instead of a HttpSessionConfig instance.
    http_client: Annotated[Optional[Dict],
                           "A http session configuration specialized for this repository"] = None


SKIP_RDI_REPORT = {
    'valid_entries': 0,
    'failed_entries': 0,
    'skipped': True
}


@traced
async def _extract_metadata(
        url: str,
        session: HttpSession,
        extractor: MetadataExtractor) -> Optional[List[Dict]]:
    """
    Extracts metadata from the specified URL.

    Parameters
    ----------
    url : str
        The URL from which to extract metadata.
    session : HttpSession
        The http session to use to download the URL content.
    extractor : MetadataExtractor
        The metadata extractor to use.

    Returns
    -------
    Optional[List[Dict]]
        A dictionary containing the extracted metadata.
    """
    otel_span = trace.get_current_span()
    otel_span.set_attribute(url_attributes.URL_FULL, url)
    try:
        content = await session.get_decoded_url(url)
        metadata = extractor.get_metadata_or_log_error(content, url)
        return metadata
    except (HttpSessionResponseError, HttpSessionDecodeError) as e:
        # These exceptions are raised by get_decoded_url.
        # Treat them as errors that only relate to single datasets and
        # skip this dataset.
        # (Same approach as get_metadata_or_log_error performs internally
        # when it encounters parsing errors)
        otel_span.record_exception(e)
        msg = "caught recoverable exception, omitting metadataset"
        otel_span.add_event(msg)
        logging.exception(msg)
        return None


@traced
async def _extract_many_metadata(
        urls: List[str],
        session: HttpSession,
        extractor: MetadataExtractor) -> Tuple[Optional[List[Dict]], Dict]:
    """
    Extracts metadata for multiple URLs asynchronously.

    Parameters
    ----------
        urls : List[str]
            A list of URLs to extract metadata from.
        session : HttpSession
            The http session to use to download the URLs content.
        extractor : MetadataExtractor
            The metadata extractor to use.

    Returns
    -------
        List[Dict]
            A list of metadata found at the specified URLs.
            Note that the metadata entries to not correspond 1:1 to the URLs. Each URL may
            include several several metadata entries or none (especially in case the
            metadata extraction failed).
    """
    otel_span = trace.get_current_span()
    extractors = [_extract_metadata(url, session, extractor) for url in urls]
    datasets = await asyncio.gather(*extractors, return_exceptions=True)
    for dataset in datasets:
        if isinstance(dataset, Exception):
            otel_span.record_exception(dataset)
            msg = "caught unrecoverable exception, omitting all metadata of RDI"
            otel_span.add_event(msg)
            logging.exception(msg)
            return None, SKIP_RDI_REPORT

    filtered_datasets = (m for m in datasets if isinstance(m, list))
    result = list(itertools.chain.from_iterable(filtered_datasets))
    report = {
        'valid_entries': len(result),
        'failed_entries': len(datasets)-len(result),
        'skipped': False
    }
    return result, report


@traced
async def scrape_repo(
        config: MetadataScraperConfig,
        default_session_config: HttpSessionConfig) -> Tuple[Optional[List[Dict]], Dict]:
    """
    Scrapes the configured repository for metadata.

    Parameters
    ----------
        config : MetadataScraperConfig
            The configuration of the repository to scrape.
        default_session_config : HttpSessionConfig
            The default http session configuration, used if not specified in the config.

    Returns
    -------
        List[Dict]
            The extracted metadata in terms of python dictonaries.
    """

    otel_span = trace.get_current_span()
    otel_span.set_attribute(
        "FAIRagro.middleware.MetadataScraper.repository_name", config.name)
    otel_span.set_attribute(
        "FAIRagro.middleware.MetadataScraper.repository_sitemap_url", config.url)
    try:
        if config.http_client:
            http_session_config = HttpSessionConfig(**config.http_client)
        else:
            http_session_config = default_session_config
        async with HttpSession(http_session_config) as session:
            sitemap_content = await session.get_decoded_url(config.url)
            parser = SitemapParser.create_instance(
                config.sitemap, sitemap_content)
            if parser.has_metadata:
                return parser.metadata

            urls = list(parser.datasets)
            if config.metadata:
                extractor = MetadataExtractor.create_instance(config.metadata)
                metadata, report = await _extract_many_metadata(urls, session, extractor)
                return metadata, report

    except (HttpSessionFetchError, SitemapParseError, MetadataParseError) as e:
        otel_span.record_exception(e)
        msg = "Could not download or parse RDI sitemap, skipping RDI"
        otel_span.add_event(msg)
        logging.exception(msg)

    return None, SKIP_RDI_REPORT
