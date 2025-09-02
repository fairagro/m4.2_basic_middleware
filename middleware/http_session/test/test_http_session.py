# """
# A test module for the http_session package.
# """

import unittest
from unittest.mock import AsyncMock, patch, MagicMock
from aiohttp import ClientError
from middleware.http_session import (
    HttpSession,
    HttpSessionTechnicalError,
    HttpSessionResponseError,
    HttpSessionDecodeError,
    HttpSessionArgumentError
)


class TestHttpSession(unittest.IsolatedAsyncioTestCase):
    """
    The main test class
    """

    async def asyncSetUp(self):
        self.session = HttpSession(config=MagicMock())

    @patch("middleware.http_session.trace.get_tracer")
    @patch("middleware.http_session.chardet.detect", return_value={"encoding": "utf-8"})
    @patch("middleware.http_session.HttpSession.get")
    async def test_http_success(self, mock_get, _mock_chardet, _mock_tracer):
        """
        test good http path
        """
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"hello world")
        mock_get.return_value = MagicMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        )

        content = await self.session.get_decoded_url("http://example.com")
        self.assertEqual(content, "hello world")

    @patch("middleware.http_session.trace.get_tracer")
    @patch("middleware.http_session.HttpSession.get")
    async def test_http_5xx_raises_technical_error(self, mock_get, _mock_tracer):
        """
        test http 5xx raises technical error
        """
        mock_response = AsyncMock()
        mock_response.status = 502
        mock_get.return_value = MagicMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        )

        with self.assertRaises(HttpSessionTechnicalError):
            await self.session.get_decoded_url("http://example.com")

    @patch("middleware.http_session.trace.get_tracer")
    @patch("middleware.http_session.HttpSession.get")
    async def test_http_4xx_raises_response_error(self, mock_get, _mock_tracer):
        """
        test http 4xx raises response error
        """
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_get.return_value = MagicMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        )

        with self.assertRaises(HttpSessionResponseError):
            await self.session.get_decoded_url("http://example.com")

    @patch("middleware.http_session.trace.get_tracer")
    @patch("middleware.http_session.HttpSession.get")
    async def test_http_network_exception(self, mock_get, _mock_tracer):
        """
        test network exception
        """
        mock_get.return_value = MagicMock(
            __aenter__=AsyncMock(side_effect=ClientError("boom")),
            __aexit__=AsyncMock(return_value=None)
        )

        with self.assertRaises(HttpSessionTechnicalError):
            await self.session.get_decoded_url("http://example.com")

    @patch("middleware.http_session.trace.get_tracer")
    @patch("middleware.http_session.aiofiles.open")
    @patch("middleware.http_session.chardet.detect", return_value={"encoding": "utf-8"})
    async def test_file_success(self, _mock_chardet, mock_aiofiles, _mock_tracer):
        """
        test good file path
        """
        mock_file = AsyncMock()
        mock_file.read = AsyncMock(return_value=b"file content")
        mock_aiofiles.return_value.__aenter__.return_value = mock_file

        content = await self.session.get_decoded_url("file:///tmp/test.txt")
        self.assertEqual(content, "file content")

    @patch("middleware.http_session.trace.get_tracer")
    async def test_unsupported_scheme_raises_argument_error(self, _mock_tracer):
        """
        test unsupported scheme raises argument error
        """
        with self.assertRaises(HttpSessionArgumentError):
            await self.session.get_decoded_url("ftp://example.com")

    @patch("middleware.http_session.trace.get_tracer")
    @patch("middleware.http_session.chardet.detect", return_value={"encoding": "utf-8"})
    @patch("middleware.http_session.HttpSession.get")
    async def test_decode_error_raises_decode_error(self, mock_get, _mock_chardet, _mock_tracer):
        """
        test decode error raises decode error
        """
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"\xff\xff")
        mock_get.return_value = MagicMock(
            __aenter__=AsyncMock(return_value=mock_response),
            __aexit__=AsyncMock(return_value=None)
        )

        with self.assertRaises(HttpSessionDecodeError):
            await self.session.get_decoded_url("http://example.com")


# import unittest
# from unittest.mock import AsyncMock, patch

# from middleware.http_session import HttpSession, HttpSessionConfig


# class TestHttpSession(unittest.IsolatedAsyncioTestCase):
#     """
#     The main test class
#     """

#     async def test_get_decoded_url(self):
#         """
#         This test was created automatically with the help of Codeium.
#         It's trivial. Better tests of HttpSession.get_decoded_url would
#         take the HttpSessionConfig into account. But this is far form
#         trivial...
#         """
#         url = "https://example.com"
#         content = b'Hello, \xe4\xb8\x96\xe7\x95\x8c!'   # corresponds to "Hello, 世界!"
#         encoding = "utf-8"
#         session_config = HttpSessionConfig(**{
#             'connection_limit': 1,
#             'receive_timeout': 10,
#             'connect_timeout': 10
#         })

#         # Mock the response object
#         response = AsyncMock()
#         response.read.return_value = content

#         # Patch the chardet.detect function to return the expected encoding
#         with patch("chardet.detect") as mock_detect:
#             mock_detect.return_value = {"encoding": encoding}

#             # Create an instance of the class
#             async with HttpSession(session_config) as session:

#                 # Patch the get method to return the mocked response
#                 with patch.object(session, "get") as mock_get:
#                     mock_get.return_value.__aenter__.return_value = response

#                     # Call the function under test
#                     decoded_content = await session.get_decoded_url(url)

#                     # Assert the decoded content
#                     self.assertEqual(decoded_content, content.decode(encoding))

#                     # Assert that the get method was called with the correct URL
#                     mock_get.assert_called_once_with(url)

#                     # Assert that the chardet.detect function was called with the correct content
#                     mock_detect.assert_called_once_with(content)
