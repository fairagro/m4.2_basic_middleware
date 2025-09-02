"""
This module defines the class HttpSession and its corresponding configuration class
HttpSessionConfig.
"""

import asyncio
from typing import Annotated, NamedTuple, Optional, Type
from types import TracebackType
from urllib.parse import urlparse
from pathlib import PurePath
from aiohttp import ClientError, ClientSession, TCPConnector, ClientTimeout
from opentelemetry import trace
from opentelemetry.semconv.attributes import url_attributes
import aiofiles
import chardet

from middleware.utils.tracer import traced


class HttpSessionConfig(NamedTuple):
    """
    A simple configuration class for the HttpSession class.
    """

    connection_limit: Annotated[int,
                                "maximum number of conconcurrent http connections"]
    receive_timeout: Annotated[int,
                               "timeout in seconds until an http connection is established"]
    connect_timeout: Annotated[int, "timeout in seconds for an http download"]


class HttpSessionFetchError(Exception):
    """Base class for fetching errors."""


class HttpSessionArgumentError(HttpSessionFetchError):
    """A input argument is not supported (aka validation error)"""


class HttpSessionTechnicalError(HttpSessionFetchError):
    """URL could not be reached at all (network, DNS, timeout)."""


class HttpSessionResponseError(HttpSessionFetchError):
    """Server/file responded with error (4xx/5xx, file not found, etc.)."""


class HttpSessionDecodeError(HttpSessionFetchError):
    """Response could not be decoded with detected encoding."""


class HttpSession(ClientSession):
    """
    A wrapper around aiohttp.ClientSession that adds the method get_decoded_url for automatic
    encoding detection (which is needed in case the website is broken).
    Additional it respects configuration in terms of an HttpSessionConfig instance.
    The URL scheme is checked before downloading. If the scheme is "file", the content is read
    from the local filesystem instead.
    """

    def __init__(self, config: HttpSessionConfig) -> None:
        """
        Initializes the HttpSession class.

        Parameters
        ----------
            config : HttpSessionConfig
                The configuration for the HttpSession class.

        Returns
        -------
            None
        """
        try:
            connector = TCPConnector(limit=config.connection_limit)
            timeout = ClientTimeout(
                # disable total timeout which might trigger if we are out of connections
                total=None,
                sock_read=config.receive_timeout,
                sock_connect=config.connect_timeout)
            super().__init__(connector=connector, timeout=timeout, raise_for_status=True)
        except Exception as e:
            raise HttpSessionArgumentError(
                "Could not create HttpSession object") from e

    async def __aenter__(self) -> "HttpSession":
        """
        Enter the context manager, returing self.

        Returns
        -------
            HttpSession
                The session itself.
        """
        await super().__aenter__()  # just in case there might be any side-effects
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> None:
        """
        Exit the context manager, not handling any exceptions.

        Parameters
        ----------
            exc_type : Optional[Type[BaseException]]
                The type of the exception being handled, if any.
            exc_val : Optional[BaseException]
                The exception instance being handled, if any.
            exc_tb : Optional[TracebackType]
                The traceback of the exception being handled, if any.

        Returns
        -------
            None
        """
        return await super().__aexit__(exc_type, exc_val, exc_tb)

    @traced
    async def get_decoded_url(self, url: str) -> str:
        """
        Fetches the content of the given URL and decodes it using the detected encoding.

        Parameters
        ----------
            url : str
                The URL to fetch the content from.

        Returns
        -------
            str
                The decoded content of the URL.
        """

        otel_span = trace.get_current_span()
        otel_span.set_attribute(url_attributes.URL_FULL, url)

        parsed_url = urlparse(url)  # does not raise
        if parsed_url.scheme in ["http", "https"]:
            try:
                async with self.get(url) as response:
                    # treat 5xx like a technical network error
                    if 500 <= response.status < 600:
                        otel_span.add_event(
                            "server reponse 5xx, raising HttpSessionTechnicalError")
                        raise HttpSessionTechnicalError(
                            f"Server error {response.status} for {url}"
                        )
                    # treat 4xx as response error
                    if 400 <= response.status < 500:
                        otel_span.add_event(
                            "server reponse 4xx, raising HttpSessionResponseError")
                        raise HttpSessionResponseError(
                            f"Server error {response.status} for {url}"
                        )
                    encoded_content = await response.read()
            except (ClientError, asyncio.TimeoutError) as e:
                otel_span.record_exception(e)
                otel_span.add_event(
                    "caught network-related exception, raising HttpSessionTechnicalError")
                raise HttpSessionTechnicalError(
                    f"Cannot fetch {url}: {e}") from e
        elif parsed_url.scheme == "file":
            try:
                # We need to deal with the following situation:
                # urlparse('file://test') => netloc = 'test', path = '', joined = 'test'
                # urlparse('file:///test') => netloc = '', path = '/test', joined = '\test'
                # urlparse('file://./test') => netloc = '.', path = '/test', joined = '\test'
                # In the last case the path is relative, so the result is wrong. Thus this code:
                base_path = PurePath(parsed_url.netloc)
                if base_path == PurePath('.'):
                    path = base_path / parsed_url.path.lstrip("/").lstrip("\\")
                else:
                    path = base_path / parsed_url.path
                async with aiofiles.open(path, 'rb') as f:
                    encoded_content = await f.read()
            except Exception as e:
                otel_span.record_exception(e)
                otel_span.add_event(
                    "caught exception when trying to read file, "
                    "raising HttpSessionResponseError")
                raise HttpSessionResponseError(
                    f"Cannot read file {url}: {e}") from e
        else:
            otel_span.add_event(
                "found unsupported URL protocol, raising HttpSessionArgumentError")
            raise HttpSessionArgumentError(
                f"Unsupported URL scheme: {parsed_url.scheme} in URL {url}")

        try:
            encoding = str(chardet.detect(encoded_content)['encoding']) or 'utf-8'
            content = encoded_content.decode(encoding)
        except Exception as e:
            otel_span.record_exception(e)
            otel_span.add_event(
                "caught exception during decoding, raising HttpSessionDecodeError")
            raise HttpSessionDecodeError(
                f"cannot decode URL content from {url}: {e}") from e

        return content
