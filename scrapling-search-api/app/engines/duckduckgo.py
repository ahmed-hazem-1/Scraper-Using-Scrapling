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
    
    def _fetch_page_content(self, url: str) -> str:
        """
        Fetch and extract full text content from a URL.
        
        Args:
            url: The URL to fetch
            
        Returns:
            str: Extracted text content, or empty string on failure
        """
        try:
            logger.debug(f"[{self.name}] Fetching content from: {url}")
            response = self.fetcher.get(url, timeout=10)
            
            if response.status != 200:
                logger.warning(f"[{self.name}] Failed to fetch {url}: status {response.status}")
                return ""
            
            # Extract text content - try to get main content areas
            # Priority: article, main, body content
            text_content = ""
            
            # Try to find article/main content first
            for selector in ['article', 'main', '[role="main"]', '.content', '#content']:
                elements = response.css(selector)
                if elements:
                    # Get all text from the element
                    texts = elements[0].css('*::text').getall()
                    text_content = ' '.join([t.strip() for t in texts if t.strip()])
                    if len(text_content) > 100:  # Only use if we got substantial content
                        break
            
            # Fallback: get all paragraph text
            if not text_content or len(text_content) < 100:
                paragraphs = response.css('p::text').getall()
                text_content = ' '.join([p.strip() for p in paragraphs if p.strip()])
            
            # Limit content size (first 5000 characters)
            if len(text_content) > 5000:
                text_content = text_content[:5000] + "..."
            
            logger.debug(f"[{self.name}] Extracted {len(text_content)} chars from {url}")
            return text_content
            
        except Exception as e:
            logger.warning(f"[{self.name}] Error fetching content from {url}: {e}")
            return ""

    def search(self, query: str, limit: int, year: int = None) -> List[SearchResult]:
        """
        Search using DuckDuckGo via Scrapling.

        Args:
            query: Search query string
            limit: Maximum number of results
            year: Optional year to filter results by

        Returns:
            List[SearchResult]: Search results
        """
        # Add year to query if specified
        search_query = f"{query} {year}" if year else query
        logger.info(f"[{self.name}] Searching for '{search_query}' (limit={limit})")

        url = f"{self.base_url}?{urllib.parse.urlencode({'q': search_query})}"

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
                # Try multiple methods to extract title
                title = None
                title_selectors = ['a.result__a', 'h2.result__title a', 'h2 a', 'a']
                for t_sel in title_selectors:
                    title_elems = element.css(t_sel)
                    if title_elems:
                        # Try to get text content
                        title_text = title_elems[0].css('::text').getall()
                        if title_text:
                            title = ' '.join([t.strip() for t in title_text if t.strip()])
                            if title:
                                logger.debug(f"[{self.name}] Result {idx}: found title with '{t_sel}': {title[:50]}")
                                break
                
                # Try multiple methods to extract URL
                url = None
                url_selectors = ['a.result__a', 'h2.result__title a', 'h2 a', 'a']
                for l_sel in url_selectors:
                    url_elems = element.css(l_sel)
                    if url_elems:
                        href = url_elems[0].attrib.get('href', '')
                        if href:
                            # Handle DuckDuckGo redirect URLs
                            if href.startswith('//duckduckgo.com/l/?') or href.startswith('/l/?'):
                                parsed = urllib.parse.urlparse(href)
                                params_dict = urllib.parse.parse_qs(parsed.query)
                                if 'uddg' in params_dict:
                                    href = urllib.parse.unquote(params_dict['uddg'][0])
                            if href.startswith('//'):
                                href = 'https:' + href
                            if href.startswith('http'):
                                url = href
                                logger.debug(f"[{self.name}] Result {idx}: found URL with '{l_sel}': {url[:80]}")
                                break

                snippet = None
                content = None
                date = None
                
                # Extract snippet from search result page  
                snippet_selectors = ['a.result__snippet', 'div.result__snippet', 'div.snippet', '.result-snippet']
                for s_sel in snippet_selectors:
                    snippet_texts = element.css(f'{s_sel} *::text').getall()
                    if snippet_texts:
                        snippet = ' '.join([t.strip() for t in snippet_texts if t.strip()])
                        if snippet:
                            logger.debug(f"[{self.name}] Result {idx}: found snippet with '{s_sel}': {snippet[:50]}")
                            break
                
                # Fetch full page content from the result URL
                content = self._fetch_page_content(url) if url else ""
                
                # Try to extract date from snippet first, then full content
                search_text = snippet if snippet else content
                if search_text:
                    # Look for common date patterns in text
                    import re
                    date_patterns = [
                        r'(?:Release date|Published|Posted|Updated):\s*([A-Za-z]+\.?\s+\d{1,2},?\s+\d{4})',
                        r'([A-Za-z]+\s+\d{1,2},?\s+\d{4})',  # e.g. "Feb. 3, 2026" or "February 3, 2026"
                        r'(\d{1,2}\s+[A-Za-z]+\s+\d{4})',  # e.g. "3 Feb 2026"
                        r'(\d{4}-\d{2}-\d{2})',  # ISO format
                    ]
                    for pattern in date_patterns:
                        match = re.search(pattern, search_text)
                        if match:
                            date = match.group(1).strip()
                            break

                # Log validation results
                if not title:
                    logger.warning(f"[{self.name}] Result {idx}: Missing title")
                if not url:
                    logger.warning(f"[{self.name}] Result {idx}: Missing URL")
                
                if not title or not url:
                    continue

                results.append(SearchResult(
                    title=title.strip(),
                    url=url.strip(),
                    snippet=snippet.strip() if snippet else "",
                    content=content.strip() if content else None,
                    date=date
                ))
                logger.debug(f"[{self.name}] Result {len(results)}: {title[:60]}")

            except Exception as e:
                logger.warning(f"[{self.name}] Failed to parse result {idx}: {type(e).__name__}: {e}")
                continue

        return results
