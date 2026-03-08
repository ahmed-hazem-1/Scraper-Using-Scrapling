"""
Google search engine implementation using Playwright.

Google requires JavaScript execution, so we use Playwright for browser automation.
Note: This is slower (~2-3s) than curl_cffi-based fetchers but necessary for Google.
"""

import time
from typing import List
import urllib.parse

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from app.config import get_logger
from app.models.schemas import SearchResult
from app.engines.base import BaseEngine

logger = get_logger(__name__)


class GoogleEngine(BaseEngine):
    """
    Google search engine using Playwright for JavaScript execution.
    Falls back gracefully if Playwright is not available.
    """

    def __init__(self, settings):
        super().__init__(settings)
        self.base_url = "https://www.google.com/search"
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("[google] Playwright not available - engine will not work")

    @property
    def name(self) -> str:
        return "google"

    def search(self, query: str, limit: int, year: int = None) -> List[SearchResult]:
        """
        Search using Google via Playwright browser automation.

        Args:
            query: Search query string
            limit: Maximum number of results
            year: Optional year to filter results by (not yet implemented)

        Returns:
            List[SearchResult]: Search results
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.error(f"[{self.name}] Playwright not available, cannot search")
            return []

        logger.info(f"[{self.name}] Searching for '{query}' (limit={limit})")

        params = urllib.parse.urlencode({'q': query, 'num': min(limit, 50), 'hl': 'en'})
        url = f"{self.base_url}?{params}"

        for attempt in range(1, self.settings.max_retries + 1):
            try:
                logger.info(f"[{self.name}] Attempt {attempt}/{self.settings.max_retries}")

                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    try:
                        page = browser.new_page()
                        
                        # Navigate to the URL
                        logger.info(f"[{self.name}] Loading Google search page...")
                        page.goto(url, wait_until='networkidle', timeout=30000)
                        
                        # Wait for search results to load
                        try:
                            page.wait_for_selector('div#search', timeout=10000)
                        except PlaywrightTimeout:
                            logger.warning(f"[{self.name}] Timeout waiting for results container")
                        
                        # Extract results from rendered page
                        results = self._parse_results_playwright(page, limit)
                        
                        if results:
                            logger.info(f"[{self.name}] Found {len(results)} results")
                            return results
                        
                        logger.warning(f"[{self.name}] No results on attempt {attempt}")
                        
                    finally:
                        browser.close()

                time.sleep(self.settings.request_delay * attempt)

            except Exception as e:
                logger.error(f"[{self.name}] Attempt {attempt} error: {e}")
                time.sleep(self.settings.request_delay * attempt)

        logger.error(f"[{self.name}] All retry attempts failed")
        return []
    
    def _parse_results_playwright(self, page, max_results: int) -> List[SearchResult]:
        """
        Parse search results from Playwright page object.

        Args:
            page: Playwright page object
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
            'div#rso > div',
        ]

        elements = []
        for selector in selectors:
            try:
                elements = page.query_selector_all(selector)
                logger.info(f"[{self.name}] Selector '{selector}': found {len(elements)} elements")
                if elements:
                    logger.info(f"[{self.name}] Using selector: '{selector}'")
                    break
            except Exception as e:
                logger.debug(f"[{self.name}] Selector '{selector}' failed: {e}")
                continue

        if not elements:
            logger.error(f"[{self.name}] No result elements found with any selector")
            return []

        for idx, element in enumerate(elements[:max_results]):
            try:
                # Extract title
                title = None
                title_selectors = ['h3', '[role="heading"]']
                for title_sel in title_selectors:
                    try:
                        title_elem = element.query_selector(title_sel)
                        if title_elem:
                            title = title_elem.inner_text()
                            if title:
                                break
                    except:
                        continue

                # Extract URL
                url = None
                try:
                    link_elem = element.query_selector('a[href]')
                    if link_elem:
                        href = link_elem.get_attribute('href')
                        if href and href.startswith('http') and 'google.com' not in href:
                            url = href
                        elif href and '/url?q=' in href:
                            url = urllib.parse.unquote(href.split('/url?q=')[1].split('&')[0])
                except:
                    pass

                # Extract snippet
                snippet = None
                snippet_selectors = ['div.VwiC3b', 'div[data-content-feature="1"]', 
                                    'span.aCOpRe', 'div.IsZvec', 'div[data-snf]']
                for snippet_sel in snippet_selectors:
                    try:
                        snippet_elem = element.query_selector(snippet_sel)
                        if snippet_elem:
                            snippet = snippet_elem.inner_text()
                            if snippet and len(snippet.strip()) > 20:
                                break
                    except:
                        continue

                if not title or not url:
                    logger.debug(f"[{self.name}] Skipping result {idx}: missing title or URL")
                    continue

                results.append(SearchResult(
                    title=title.strip(),
                    url=url.strip(),
                    snippet=snippet.strip() if snippet else "",
                    content=None,
                    date=None
                ))
                logger.debug(f"[{self.name}] Result {len(results)}: {title[:60]}")

            except Exception as e:
                logger.debug(f"[{self.name}] Failed to parse result {idx}: {e}")
                continue

        return results
