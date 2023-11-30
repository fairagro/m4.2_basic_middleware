import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from http_session import HttpSession, HttpSessionConfig

class TestGetDecodedUrl(unittest.IsolatedAsyncioTestCase):
    async def test_get_decoded_url(self):
        url = "https://example.com"
        content = b"Hello, World!"
        encoding = "utf-8"
        session_config = HttpSessionConfig(**{
            'connection_limit': 1,
            'receive_timeout': 10,
            'connect_timeout': 10
        })

        # Mock the response object
        response = AsyncMock()
        response.read.return_value = content

        # Patch the chardet.detect function to return the expected encoding
        with patch("chardet.detect") as mock_detect:
            mock_detect.return_value = {"encoding": encoding}

            # Create an instance of the class
            session = HttpSession(session_config)

            # Patch the get method to return the mocked response
            with patch.object(session, "get") as mock_get:
                mock_get.return_value.__aenter__.return_value = response

                # Call the function under test
                decoded_content = await session.get_decoded_url(url)

                # Assert the decoded content
                self.assertEqual(decoded_content, content.decode(encoding))

                # Assert that the get method was called with the correct URL
                mock_get.assert_called_once_with(url)

                # Assert that the chardet.detect function was called with the correct content
                mock_detect.assert_called_once_with(content)