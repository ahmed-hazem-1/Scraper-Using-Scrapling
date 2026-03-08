from typing import List
from urllib.parse import quote_plus
from scrapling import Fetcher
from app.config import get_logger
from app.models.schemas import SearchResult
from app.engines.base import BaseEngine
from app.services.url_service import is_valid_search_result_url, extract_bing_url

logger = get_logger(__name__)

class BingEngine(BaseEngine):

    @property
    def name(self) -> str:
        return "bing"

    def __init__(self, settings):
        super().__init__(settings)
        self.fetcher = Fetcher()
        # Configure Fetcher with Chrome impersonation for stealth
        self.fetcher.configure(browser='chrome', os='windows', http_version=2)

    def search(self, query: str, limit: int, year: int = None) -> List[SearchResult]:
        # Note: year parameter not yet implemented for Bing
        logger.info(f"[{self.name}] Searching for '{query}' (limit={limit})")
        is_arabic = any('\u0600' <= c <= '\u06FF' for c in query)
        locale = "ar-EG" if is_arabic else "en-US"
        search_url = f"https://www.bing.com/search?q={quote_plus(query)}&count={limit}&setlang={locale}&mkt={locale}&cc=EG"
        try:
            # Fetch with configured browser fingerprint
            page = self.fetcher.get(
                url=search_url,
                follow_redirects=True,
                timeout=30
            )
            results = self._parse_results(page, limit)
            logger.info(f"[{self.name}] Found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"[{self.name}] Search failed: {type(e).__name__}: {e}")
            raise

    def _parse_results(self, page, max_results: int) -> List[SearchResult]:
        results = []
        try:
            # Debug: Log HTML snippet to check page structure
            html_snippet = str(page.html)[:500] if hasattr(page, 'html') else str(page)[:500]
            logger.info(f"[bing] HTML snippet: {html_snippet}")
            
            result_elements = page.css('li.b_algo')
            logger.info(f"[{self.name}] Found {len(result_elements)} result elements with 'li.b_algo'")
            
            # Debug: Try alternative selectors
            if len(result_elements) == 0:
                alt1 = page.css('.b_algo')
                alt2 = page.css('li[class*="algo"]')
                alt3 = page.css('.b_results .b_algo')
                logger.info(f"[bing] Alternative selectors: .b_algo={len(alt1)}, li[class*='algo']={len(alt2)}, .b_results .b_algo={len(alt3)}")
            
            for idx, elem in enumerate(result_elements):
                if len(results) >= max_results:
                    break
                try:
                    title_elems = elem.css('h2 a')
                    if not title_elems:
                        logger.info(f"[bing] Result {idx}: No title elements found")
                        continue
                    
                    # Try multiple ways to extract title text
                    title_elem = title_elems[0]
                    title = None
                    
                    # Method 1: .text attribute
                    if hasattr(title_elem, 'text') and title_elem.text:
                        title = title_elem.text.strip() if isinstance(title_elem.text, str) else str(title_elem.text).strip()
                    
                    # Method 2: .text_content() method (like lxml)
                    if not title and hasattr(title_elem, 'text_content'):
                        title = title_elem.text_content().strip()
                    
                    # Method 3: Direct string conversion
                    if not title:
                        title = str(title_elem).strip()
                        # Extract text from HTML if needed
                        import re
                        text_match = re.search(r'>([^<]+)<', title)
                        if text_match:
                            title = text_match.group(1).strip()
                    
                    logger.info(f"[bing] Result {idx}: Extracted title='{title[:50] if title else title}'")
                    
                    raw_url = title_elem.attrib.get('href', '')
                    logger.info(f"[bing] raw_url = {raw_url[:120]}")
                    url = extract_bing_url(raw_url)
                    logger.info(f"[bing] decoded_url = {url[:120]}")
                    snippet_elems = elem.css('.b_caption p')
                    snippet = snippet_elems[0].text if snippet_elems else ""
                    
                    # Debug validation
                    logger.info(f"[bing] Result {idx}: title='{title}', title_valid={bool(title)}, url_valid={is_valid_search_result_url(url)}")
                    
                    if title and is_valid_search_result_url(url):
                        # Note: Bing doesn't provide extended content/dates in same format as DDG
                        results.append(SearchResult(
                            title=title, 
                            snippet=snippet, 
                            url=url,
                            content=None,
                            date=None
                        ))
                        logger.info(f"[bing] Result {idx}: ADDED to results")
                    else:
                        logger.info(f"[bing] Result {idx}: REJECTED - title={bool(title)}, url_valid={is_valid_search_result_url(url)}")
                except Exception as e:
                    logger.info(f"[{self.name}] Failed to parse result {idx}: {e}")
                    continue
        except Exception as e:
            logger.error(f"[{self.name}] Failed to parse page: {e}")
        return results
