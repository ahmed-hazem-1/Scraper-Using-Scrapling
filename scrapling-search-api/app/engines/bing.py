"""
Bing search engine implementation.
"""

from typing import List
from urllib.parse import quote_plus

import httpx
from lxml import html as lxml_html

from app.config import get_logger
from app.models.schemas import SearchResult
from app.engines.base import BaseEngine
from app.services.url_service import is_valid_search_result_url, extract_bing_url

logger = get_logger(__name__)


class BingEngine(BaseEngine):
    """
    Bing search engine implementation.
    
    Uses Bing's HTML search interface.
    """
    
    @property
    def name(self) -> str:
        """Get engine name."""
        return "bing"
    
    def search(self, query: str, limit: int) -> List[SearchResult]:
        """
        Search using Bing.
        
        Args:
            query: Search query string
            limit: Maximum number of results
        
        Returns:
            List[SearchResult]: Search results
        
        Raises:
            Exception: If search fails
        """
        logger.info(f"[{self.name}] Searching for '{query}' (limit={limit})")
        
        search_url = f"https://www.bing.com/search?q={quote_plus(query)}"
        
        try:
            # Fetch HTML
            html = self._fetch_html(search_url)
            
            # Parse results
            results = self._parse_results(html, limit)
            
            logger.info(f"[{self.name}] Found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"[{self.name}] Search failed: {e}")
            raise
    
    def _fetch_html(self, url: str) -> str:
        """
        Fetch HTML from URL with realistic browser headers.
        
        Args:
            url: URL to fetch
        
        Returns:
            str: HTML content
        """
        headers = {
            'User-Agent': self.settings.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        
        with httpx.Client(timeout=self.settings.http_timeout) as client:
            response = client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
        
        return response.text
    
    def _parse_results(self, html: str, max_results: int) -> List[SearchResult]:
        """
        Parse search results from Bing HTML.
        
        Args:
            html: HTML content
            max_results: Maximum number of results to extract
        
        Returns:
            List[SearchResult]: Parsed results
        """
        results = []
        
        try:
            tree = lxml_html.fromstring(html)
            
            # Bing uses .b_algo for organic search results
            result_elements = tree.cssselect('.b_algo')
            
            logger.debug(f"[{self.name}] Found {len(result_elements)} result elements")
            
            for idx, elem in enumerate(result_elements):
                if len(results) >= max_results:
                    break
                
                try:
                    # Extract title and URL from h2 > a
                    title_elems = elem.cssselect('h2 a')
                    if not title_elems:
                        continue
                    
                    title = title_elems[0].text_content().strip()
                    bing_redirect_url = title_elems[0].get('href', '')
                    
                    # Extract actual URL from Bing redirect
                    url = extract_bing_url(bing_redirect_url)
                    
                    # Extract snippet from .b_caption p
                    snippet_elems = elem.cssselect('.b_caption p')
                    snippet = snippet_elems[0].text_content().strip() if snippet_elems else ""
                    
                    # Validate
                    if title and is_valid_search_result_url(url):
                        results.append(SearchResult(
                            title=title,
                            snippet=snippet,
                            url=url
                        ))
                
                except Exception as e:
                    logger.debug(f"[{self.name}] Failed to parse result {idx}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"[{self.name}] Failed to parse HTML: {e}")
        
        return results
