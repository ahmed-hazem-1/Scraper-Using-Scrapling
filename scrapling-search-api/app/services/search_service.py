"""
Search service with multi-engine support.

This module provides the main search functionality with:
- Multiple search engines (DuckDuckGo, Bing, Google)
- Automatic fallback between engines
- Source filtering
- Error handling
"""

from typing import List, Optional

from app.config import Settings, get_logger
from app.models.schemas import SearchResult, SearchResponse
from app.engines.manager import EngineManager
from app.services.url_service import matches_sources

logger = get_logger(__name__)


class SearchService:
    """
    High-level search service with multi-engine support and source filtering.
    
    This service orchestrates search operations across multiple engines
    (DuckDuckGo, Bing, Google) with automatic fallback and source filtering.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize the search service.
        
        Args:
            settings: Application settings instance
        """
        self.settings = settings
        self.engine_manager = EngineManager(settings)
        logger.info("SearchService initialized with multi-engine support")
    
    def search(
        self, 
        query: str, 
        limit: int, 
        sources: Optional[List[str]] = None,
        preferred_engine: Optional[str] = None,
        strict_mode: bool = False
    ) -> SearchResponse:
        """
        Perform a web search with automatic engine fallback.
        
        This method:
        1. Tries preferred engine first (if specified)
        2. Falls back to other engines if rate limited or failed (unless strict_mode)
        3. Applies source filtering to results
        4. Returns results with engine information
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            sources: Optional list of domain names to filter results by
            preferred_engine: Optional preferred engine name ("duckduckgo", "bing", or "google")
            strict_mode: If True, only try the preferred engine (no fallback)
        
        Returns:
            SearchResponse: Search response with results and metadata
        """
        sources_info = f", sources={sources}" if sources else ""
        engine_info = f", preferred_engine={preferred_engine}" if preferred_engine else ""
        strict_info = ", strict_mode=True" if strict_mode else ""
        logger.info(f"Search request: query='{query}', limit={limit}{sources_info}{engine_info}{strict_info}")
        
        try:
            # Search using EngineManager (handles fallback automatically)
            results, engine_used = self.engine_manager.search(
                query=query,
                limit=limit,
                preferred_engine=preferred_engine,
                strict_mode=strict_mode
            )
            
            # Apply source filtering if specified
            if sources:
                filtered_results = [
                    result for result in results
                    if matches_sources(result.url, sources)
                ]
                
                if len(filtered_results) < len(results):
                    logger.info(
                        f"Source filtering: {len(results)} → {len(filtered_results)} results "
                        f"(sources: {sources})"
                    )
                
                results = filtered_results
            
            # Build successful response
            response = SearchResponse(
                query=query,
                count=len(results),
                results=results,
                sources=sources,
                engine_used=engine_used,
                error=None
            )
            
            logger.info(
                f"Search completed: {len(results)} results from {engine_used}"
            )
            return response
            
        except Exception as e:
            # Build error response
            error_message = f"All engines failed: {str(e)}"
            logger.error(error_message, exc_info=True)
            
            response = SearchResponse(
                query=query,
                count=0,
                results=[],
                sources=sources,
                engine_used=None,
                error=error_message
            )
            
            return response
