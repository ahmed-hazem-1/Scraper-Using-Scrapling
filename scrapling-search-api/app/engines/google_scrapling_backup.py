"""
Google search engine implementation using Scrapling.

Uses Scrapling's StealthyFetcher to bypass Google's bot detection.
"""

import time
from typing import List
import urllib.parse

from scrapling import Fetcher

from app.config import get_logger
from app.models.schemas import SearchResult
from app.engines.base import BaseEngine

logger = get_logger(__name__)


class GoogleEngine(BaseEngine):
    """
    Google search engine using Scrapling's Fetcher (curl_cffi-based) for anti-bot detection bypass.
    """

    def __init__(self, settings):
        super().__init__(settings)
        self.fetcher = Fetcher()
        self.base_url = "https://www.google.com/search"

    @property
    def name(self) -> str:
        """Get engine name."""
        return "google"

    def search(self, query: str, limit: int) -> List[SearchResult]:
        """
        Search using Google via Scrapling.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List[SearchResult]: Search results
        """
        logger.info(f"[{self.name}] Searching for '{query}' (limit={limit})")

        params = urllib.parse.urlencode({'q': query, 'num': min(limit, 50), 'hl': 'en'})
        url = f"{self.base_url}?{params}"

        for attempt in range(1, self.settings.max_retries + 1):
            try:
                logger.info(f"[{self.name}] Attempt {attempt}/{self.settings.max_retries}")

                page = self.fetcher.get(url)
                logger.info(f"[{self.name}] Response status: {page.status}")

                if page.status != 200:
                    logger.warning(f"[{self.name}] Non-200 status: {page.status}")
                    time.sleep(self.settings.request_delay * attempt)
                    continue

                results = self._parse_results(page, limit)

                if results:
                    logger.info(f"[{self.name}] Found {len(results)} results")
                    return results

                logger.warning(f"[{self.name}] No results on attempt {attempt}")
                time.sleep(self.settings.request_delay * attempt)

            except Exception as e:
                logger.error(f"[{self.name}] Attempt {attempt} error: {e}")
                time.sleep(self.settings.request_delay * attempt)

        logger.error(f"[{self.name}] All retry attempts failed")
        return []
    
    def _parse_results(self, page, max_results: int) -> List[SearchResult]:
        """
        Parse search results from Scrapling page object.

        Args:
            page: Scrapling page object
            max_results: Maximum number of results to extract

        Returns:
            List[SearchResult]: Parsed results
        """
        results = []

        # Try multiple selectors - Google changes DOM frequently
        selectors = [
            'div.g',
            'div[data-sokoban-container]',
            'div.Gx5Zad',
            'div:has(h3)',
        ]

        result_elements = []
        for selector in selectors:
            elements = page.css(selector)
            logger.info(f"[{self.name}] Selector '{selector}': found {len(elements)} elements")
            if elements:
                result_elements = elements
                logger.info(f"[{self.name}] Using selector: '{selector}'")
                break

        if not result_elements:
            logger.error(f"[{self.name}] No result elements found with any selector")
            return []

        for idx, element in enumerate(result_elements[:max_results]):
            try:
                # Extract title
                title = None
                for title_sel in ['h3::text', 'h3 *::text', '[role="heading"]::text']:
                    title = element.css(title_sel).get()
                    if title:
                        break

                # Extract URL
                url = None
                for link_sel in ['a::attr(href)', 'a[href]::attr(href)']:
                    href = element.css(link_sel).get()
                    if href and href.startswith('http') and 'google.com' not in href:
                        url = href
                        break
                    elif href and '/url?q=' in href:
                        url = urllib.parse.unquote(href.split('/url?q=')[1].split('&')[0])
                        break

                # Extract snippet
                snippet = None
                for snippet_sel in ['div.VwiC3b::text', 'div[data-content-feature="1"]::text',
                                    'span.aCOpRe::text', 'div.IsZvec::text']:
                    snippet = element.css(snippet_sel).get()
                    if snippet and len(snippet.strip()) > 20:
                        break

                if not title or not url:
                    logger.debug(f"[{self.name}] Skipping result {idx}: missing title or URL")
                    continue

                results.append(SearchResult(
                    title=title.strip(),
                    url=url.strip(),
                    snippet=snippet.strip() if snippet else ""
                ))
                logger.debug(f"[{self.name}] Result {len(results)}: {title[:60]}")

            except Exception as e:
                logger.debug(f"[{self.name}] Failed to parse result {idx}: {e}")
                continue

        return results
