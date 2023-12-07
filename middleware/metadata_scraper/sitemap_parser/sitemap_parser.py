"""
This module define the abtract base class for sitemap parsers.
"""

from typing import List
import json

from utils.registering_abc import RegisteringABC


class SitemapParseError(RuntimeError):
    """
    An excpetion of this type will be thrown by implementations of SitemapParser
    if the content cannot be parsed.
    """

    def __init__(self, inner_exception: Exception) -> None:
        super().__init__(f"Failed to parse metadata: {inner_exception}")
        self.inner_exception = inner_exception


class SitemapParser(RegisteringABC):
    """
    An abstract base class for sitemap parsers.
    It will abstract away the type of sitemap (xml, json, etc.).
    """

    def __init__(self, content: str) -> None:
        """
        Initializes the sitemap parser. Essentially stores the content.
        """
        self._content = content

    @property
    def content(self) -> str:
        """
        Returns the content of the sitemap.
        """
        return self._content

    @property
    def metadata(self) -> List[dict]:
        """
        Return the metadata in case it is already included in the sitemap.
        Will raise an exception of type 'MetadataParseError' if the metadata cannot be parsed.
        
        Returns
        -------
            List[dict]
                The metadata in terms of a list of dictionaries.
        """
        if not self.content:
            # we treat empty content as an error because to be consistent with the
            # extruct library
            raise SitemapParseError("Empty content")
        metadata = self.get_metadata()
        if not isinstance(metadata, list):
            return [metadata]
        return metadata

    @property
    def datasets(self) -> str:
        """
        A generator method that returns the URLs to all datasets of the repository.
        Defaults to yield nothing.

        Yields
        ------
            str
                A string with the URL to the next dataset.
        """
        yield from []

    @property
    def has_metadata(self) -> bool:
        """
        A method that returns whether the "sitemap" already contains all needed metadata.
        Defaults to return False.

        Returns
        -------
            bool
                Flag indicating whether the "sitemap" already contains all needed metadata.
        """
        return False

    def get_metadata(self) -> List[dict]:
        """
        Returns the metadata in case it is already included in the "sitemap".
        Will raise an exception of type 'MetadataParseError' if the metadata cannot be parsed.
        Defaults to return an empty array.

        Returns
        -------
            List[dict]
                A list of dictionaries containing the extracted metadata.
        """
        return []

    def parse_content_as_json(self) -> List[dict]:
        """
        A utility method to be used by implementations of SitemapParser when overriding
        'get_metadata'. It will parse the sitempa content as JSON and return the result.

        Returns
        -------
            List[dict]
                A list of dictionaries containing the parsed JSON.
        """
        try:
            json_objs = json.loads(self.content)
        except json.JSONDecodeError as e:
            raise SitemapParseError(e) from e
        return json_objs
