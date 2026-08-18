"""
This module defines an implementation of SitemapParser that parses text sitemaps
as returned by the research repository OpenAgrar.

NOTE: OpenAgrar uses Cloudflare protection that blocks automated access.
The sitemap URL requires JavaScript challenge resolution, which cannot be
handled with standard HTTP clients. If Cloudflare challenge is detected,
the harvest will be skipped with a clear error message.
"""

__all__ = []
__version__ = '0.1.0'
__author__ = 'brizuela@ipk-gatersleben.de'


from collections.abc import Iterator
import json
import logging

from middleware.metadata_scraper.sitemap_parser.sitemap_parser import (
    SitemapParseError, SitemapParser)


logger = logging.getLogger(__name__)

BASE_URL = 'https://www.openagrar.de/receive/'


def _is_cloudflare_challenge(content: str) -> bool:
    """
    Detect if the response is a Cloudflare JavaScript challenge page.
    
    Cloudflare protection returns HTML with specific indicators that
    cannot be bypassed without a headless browser.
    """
    indicators = [
        "security check",
        "sicherheitsüberprüfung",
        "cf_challenge",
        "cf-turnstile",
        "cf-mitigated",
        "cloudflare",
        "just a moment",
    ]
    content_lower = content.lower()
    return any(ind in content_lower for ind in indicators)


class SitemapParserOpenAgrar(SitemapParser):
    """
    An implementation class of SitemapParser that parses text sitemaps as returned by OpenAgrar
    """

    @property
    def datasets(self) -> Iterator[str]:
        """
        A generator method that returns the URLs to all datasets of the repository.

        Parameters
        ----------
            content : str
                The contents of the sitemap to be parsed.

        Yields
        ------
            str
                A string with the URL to the next dataset.
        """
        try:
            if _is_cloudflare_challenge(self.content):
                raise SitemapParseError(
                    "Cloudflare JavaScript challenge detected at OpenAgrar. "
                    "Automated access is blocked. Requires headless browser or manual API access."
                )
            
            json_objs = json.loads(self.content)
            mods_ids = [doc['id'] for doc in json_objs['response']['docs']]
            for mid in mods_ids:
                yield f"{BASE_URL}{mid}"
        except SitemapParseError:
            raise
        except Exception as e:
            raise SitemapParseError(
                "Could not parse OpenAgrar sitemap") from e
