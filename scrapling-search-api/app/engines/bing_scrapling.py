"""
Bing search engine implementation using Scrapling.

Uses Scrapling's StealthyFetcher (Playwright-based) for advanced bot detection bypass.
"""

import time
from typing import List
from urllib.parse import quote_plus

from scrapling import Fetcher

from app.config import get_logger
from app.models.schemas import SearchResult
from app.engines.base import BaseEngine
from app.services.url_service import is_valid_search_result_url, extract_bing_url

logger = get_logger(__name__)


class BingEngine(BaseEngine):
    """
    Bing search engine using Scrapling's Fetcher (curl_cffi-based).
    Note: Bing has sophisticated bot detection - DuckDuckGo recommended for better accuracy.
    """

    def __init__(self, settings):
        super().__init__(settings)
        self.fetcher = Fetcher()
        self.base_url = "https://www.bing.com/search"

    @property
    def name(self) -> str:
        """Get engine name."""
        return "bing"

    def search(self, query: str, limit: int) -> List[SearchResult]:
        """
        Search using Bing via Scrapling.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List[SearchResult]: Search results
        """
        logger.info(f"[{self.name}] Searching for '{query}' (limit={limit})")

        url = f"{self.base_url}?q={quote_plus(query)}&setlang=en-US&mkt=en-US"

        for attempt in range(1, self.settings.max_retries + 1):
            try:
                logger.info(f"[{self.name}] Attempt {attempt}/{self.settings.max_retries}")
                if attempt > 1:
                    delay = self.settings.request_delay * attempt
                    logger.info(f"[{self.name}] Waiting {delay}s before retry...")
                    time.sleep(delay)

                page = self.fetcher.get(url)
                logger.info(f"[{self.name}] Response status: {page.status}")

                if page.status == 403:
                    logger.warning(f"[{self.name}] Forbidden (HTTP 403)")
                    time.sleep(5)
                    continue
                if page.status == 429:
                    logger.warning(f"[{self.name}] Rate limited (HTTP 429)")
                    time.sleep(10)
                    continue
                if page.status != 200:
                    logger.warning(f"[{self.name}] Non-200 status: {page.status}")
                    time.sleep(self.settings.request_delay * attempt)
                    continue

                results = self._parse_results(page, limit)
                if results:
                    logger.info(f"[{self.name}] Found {len(results)} results")
                    return results
                logger.warning(f"[{self.name}] No results on attempt {attempt}")
                time.sleep(self.settings.request_delay)

            except Exception as e:
                logger.error(f"[{self.name}] Attempt {attempt} error: {e}")
                time.sleep(self.settings.request_delay * attempt)

        logger.error(f"[{self.name}] All retry attempts failed")
        return []

    def _parse_results(self, page, max_results: int) -> List[SearchResult]:
        """
        Parse search results from a Scrapling page object.

        Args:
            page: Scrapling fetcher response
            max_results: Maximum number of results to extract

        Returns:
            List[SearchResult]: Parsed results
        """
        results = []
        
        # Bing uses .b_algo for organic search results
        result_elements = page.css('.b_algo')
        logger.info(f"[{self.name}] Found {len(result_elements)} .b_algo elements")

        if not result_elements:
            logger.error(f"[{self.name}] No result elements found")
            return []

        for idx, element in enumerate(result_elements[:max_results]):
            try:
                # Extract title and URL from h2 > a
                title = element.css('h2 a::text').get()
                bing_redirect_url = element.css('h2 a::attr(href)').get()
                
                if not title or not bing_redirect_url:
                    logger.debug(f"[{self.name}] Result {idx}: Missing title or URL")
                    continue
                
                # Extract actual URL from Bing redirect
                url = extract_bing_url(bing_redirect_url)
                
                # Extract snippet from .b_caption p
                snippet = element.css('.b_caption p::text').get()
                
                # Validate URL
                if not is_valid_search_result_url(url):
                    logger.debug(f"[{self.name}] Result {idx}: Invalid URL: {url}")
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
