"""
DuckDuckGo search engine implementation using Scrapling.

Uses Scrapling's StealthyFetcher to avoid rate limiting and bot detection.
"""

import time
from typing import List
import urllib.parse

from scrapling import Fetcher

from app.config import get_logger
from app.models.schemas import SearchResult
from app.engines.base import BaseEngine

logger = get_logger(__name__)


class DuckDuckGoEngine(BaseEngine):
    """
    DuckDuckGo search engine using Scrapling's Fetcher (curl_cffi-based) for rate-limit bypass.
    """

    def __init__(self, settings):
        super().__init__(settings)
        self.fetcher = Fetcher()
        self.base_url = "https://html.duckduckgo.com/html/"

    @property
    def name(self) -> str:
        """Get engine name."""
        return "duckduckgo"

    def search(self, query: str, limit: int) -> List[SearchResult]:
        """
        Search using DuckDuckGo via Scrapling.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List[SearchResult]: Search results
        """
        logger.info(f"[{self.name}] Searching for '{query}' (limit={limit})")

        url = f"{self.base_url}?{urllib.parse.urlencode({'q': query})}"

        for attempt in range(1, self.settings.max_retries + 1):
            try:
                logger.info(f"[{self.name}] Attempt {attempt}/{self.settings.max_retries}")
                if attempt > 1:
                    delay = self.settings.request_delay * attempt
                    logger.info(f"[{self.name}] Waiting {delay}s before retry...")
                    time.sleep(delay)

                page = self.fetcher.get(url)
                logger.info(f"[{self.name}] Response status: {page.status}")

                if page.status == 202:
                    logger.warning(f"[{self.name}] Rate limited (HTTP 202)")
                    time.sleep(5)
                    continue
                if page.status == 403:
                    logger.warning(f"[{self.name}] Forbidden (HTTP 403)")
                    time.sleep(5)
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
        selectors = ['div.result', 'div.results_links', 'div.web-result', 'div[class*="result"]']
        result_elements = []

        for selector in selectors:
            elements = page.css(selector)
            logger.info(f"[{self.name}] Selector '{selector}': found {len(elements)} elements")
            if elements:
                result_elements = elements
                logger.info(f"[{self.name}] Using selector: '{selector}'")
                break

        if not result_elements:
            logger.error(f"[{self.name}] No result elements found")
            return []

        for idx, element in enumerate(result_elements[:max_results]):
            try:
                title = None
                for t_sel in ['a.result__a::text', 'h2.result__title::text', 'a::text']:
                    title = element.css(t_sel).get()
                    if title:
                        break

                url = None
                for l_sel in ['a.result__a::attr(href)', 'a::attr(href)']:
                    href = element.css(l_sel).get()
                    if href:
                        if href.startswith('//duckduckgo.com/l/?'):
                            parsed = urllib.parse.urlparse(href)
                            params_dict = urllib.parse.parse_qs(parsed.query)
                            if 'uddg' in params_dict:
                                href = urllib.parse.unquote(params_dict['uddg'][0])
                        if href.startswith('//'):
                            href = 'https:' + href
                        if href.startswith('http'):
                            url = href
                            break

                snippet = None
                for s_sel in ['a.result__snippet::text', 'div.result__snippet::text', 'div.snippet::text']:
                    snippet = element.css(s_sel).get()
                    if snippet and len(snippet.strip()) > 10:
                        break

                if not title or not url:
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
