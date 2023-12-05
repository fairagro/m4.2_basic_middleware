"""
This module defines the class HttpSession and its corresponding configuration class
HttpSessionConfig.
"""

from typing import Annotated, NamedTuple, Optional, Type
from types import TracebackType
from aiohttp import ClientSession, TCPConnector, ClientTimeout
import chardet


class HttpSessionConfig(NamedTuple):
    """
    A simple configuration class for the HttpSession class.
    """

    connection_limit: Annotated[int, "maximum number of conconcurrent http connections"]
    receive_timeout: Annotated[int, "timeout in seconds until an http connection is established"]
    connect_timeout: Annotated[int, "timeout in seconds for an http download"]


class HttpSession(ClientSession):
    """
    A wrapper around aiohttp.ClientSession that adds the method get_decoded_url for automatic
    encoding detection (which is needed in case the website is broken).
    Additional it respects configuration in terms of an HttpSessionConfig instance.
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
        connector = TCPConnector(limit=config.connection_limit)
        timeout = ClientTimeout(
            total=None, # disable total timeout as this might trigger if we are out of connections
            sock_read=config.receive_timeout,
            sock_connect=config.connect_timeout)
        super().__init__(connector=connector, timeout=timeout, raise_for_status=True)

    async def __aenter__(self) -> "HttpSession":
        """
        Enter the context manager, returing self.

        Returns
        -------
            HttpSession
                The session itself.
        """
        await super().__aenter__() # just in case there might be any side-effects
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
        async with self.get(url) as response:
            content = await response.read()
            encoding = chardet.detect(content)['encoding']
            decoded_content = content.decode(encoding)
            return decoded_content
