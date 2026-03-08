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

    def search(self, query: str, limit: int) -> List[SearchResult]:
        logger.info(f"[{self.name}] Searching for '{query}' (limit={limit})")
        search_url = f"https://www.bing.com/search?q={quote_plus(query)}&count={limit}"
        try:
            page = self.fetcher.get(search_url)
            results = self._parse_results(page, limit)
            logger.info(f"[{self.name}] Found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"[{self.name}] Search failed: {e}")
            raise

    def _parse_results(self, page, max_results: int) -> List[SearchResult]:
        results = []
        try:
            result_elements = page.css('li.b_algo')
            logger.debug(f"[{self.name}] Found {len(result_elements)} result elements")
            for idx, elem in enumerate(result_elements):
                if len(results) >= max_results:
                    break
                try:
                    title_elems = elem.css('h2 a')
                    if not title_elems:
                        continue
                    title = title_elems[0].text
                    raw_url = title_elems[0].attrib.get('href', '')
                    url = extract_bing_url(raw_url)
                    snippet_elems = elem.css('.b_caption p')
                    snippet = snippet_elems[0].text if snippet_elems else ""
                    if title and is_valid_search_result_url(url):
                        results.append(SearchResult(title=title, snippet=snippet, url=url))
                except Exception as e:
                    logger.debug(f"[{self.name}] Failed to parse result {idx}: {e}")
                    continue
        except Exception as e:
            logger.error(f"[{self.name}] Failed to parse page: {e}")
        return results
