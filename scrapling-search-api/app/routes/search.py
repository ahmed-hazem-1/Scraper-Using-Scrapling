"""
Search API routes.

This module provides endpoints for web search functionality.
"""

from fastapi import APIRouter, Query, Depends
from app.models.schemas import SearchResponse, APIInfo
from app.services.search_service import SearchService
from app.config import Settings, get_settings, get_logger

logger = get_logger(__name__)

# Create router
router = APIRouter(tags=["Search"])


def get_search_service(settings: Settings = Depends(get_settings)) -> SearchService:
    """
    Dependency injection for SearchService.
    
    This creates a new SearchService instance for each request with
    the current application settings.
    
    Args:
        settings: Application settings (injected)
    
    Returns:
        SearchService: Initialized search service
    """
    return SearchService(settings)


@router.get(
    "/",
    response_model=APIInfo,
    summary="API Information",
    description="Get information about the API and available endpoints"
)
async def root(settings: Settings = Depends(get_settings)) -> APIInfo:
    """
    Root endpoint providing API information.
    
    Returns basic information about the API including:
    - API name and version
    - Available endpoints
    - Documentation link
    
    Returns:
        APIInfo: API information
    """
    logger.debug("Root endpoint requested")
    
    return APIInfo(
        name=settings.api_title,
        version=settings.api_version,
        endpoints={
            "health": "/health",
            "search": "/search?q={query}&limit={limit}&sources={sources}&engine={engine}"
        },
        documentation="/docs"
    )


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Web Search",
    description="Search the web using multiple engines (DuckDuckGo, Bing, Google) with automatic fallback, optionally filtered by source domains"
)
async def search(
    q: str = Query(
        ...,
        description="Search query string",
        min_length=1,
        max_length=500,
        example="python programming"
    ),
    limit: int = Query(
        default=None,
        description="Maximum number of results to return",
        ge=1,
        le=None,  # Will use settings.max_search_limit
        example=10
    ),
    sources: str = Query(
        default=None,
        description="Comma-separated list of source domains to filter by (e.g., 'python.org,github.com')",
        example="python.org,github.com"
    ),
    engine: str = Query(
        default=None,
        description="Preferred search engine: 'duckduckgo', 'bing', or 'google'. If not specified or fails, other engines are tried automatically.",
        example="duckduckgo"
    ),
    strict: bool = Query(
        default=False,
        description="Strict mode: only use specified engine, no fallback. Requires 'engine' parameter.",
        example=False
    ),
    year: int = Query(
        default=None,
        description="Filter results by year (e.g., 2026). Adds year to query and filters results.",
        ge=2000,
        le=2100,
        example=2026
    ),
    settings: Settings = Depends(get_settings),
    search_service: SearchService = Depends(get_search_service)
) -> SearchResponse:
    """
    Search endpoint with multi-engine support.
    
    This endpoint performs a web search and returns structured results including:
    - Page titles
    - Descriptions/snippets
    - URLs
    
    The search uses multiple engines with automatic fallback:
    1. Tries preferred engine first (if specified)
    2. Falls back to other engines if rate limited or failed
    3. Returns results from the first successful engine
    
    Results can be filtered by source domains.
    
    Args:
        q: Search query (required, 1-500 characters)
        limit: Maximum results (optional, default from settings, max 50)
        sources: Comma-separated domain list (optional, e.g., "python.org,github.com")
        engine: Preferred search engine (optional, 'duckduckgo'/'bing'/'google')
        settings: Application settings (injected)
        search_service: Search service instance (injected)
    
    Returns:
        SearchResponse: Search results with engine_used field or error information
    
    Examples:
        GET /search?q=python&limit=5
        GET /search?q=python&limit=5&sources=python.org,github.com
        GET /search?q=python&limit=5&engine=bing
    """
    # Use default limit if not specified
    if limit is None:
        limit = settings.default_search_limit
    
    # Enforce maximum limit
    limit = min(limit, settings.max_search_limit)
    
    # Parse sources parameter (comma-separated string to list)
    sources_list = None
    if sources:
        sources_list = [s.strip() for s in sources.split(',') if s.strip()]
        logger.info(f"Filtering by sources: {sources_list}")
    
    # Log search parameters
    engine_info = f", engine={engine}" if engine else ""
    year_info = f", year={year}" if year else ""
    logger.info(f"Search endpoint called: query='{q}', limit={limit}{engine_info}{year_info}")
    
    try:
        # Perform search using the search service with multi-engine support
        response = search_service.search(
            query=q, 
            limit=limit, 
            sources=sources_list,
            preferred_engine=engine,
            strict_mode=strict,
            year=year
        )
        return response
        
    except Exception as e:
        # Log error and return error response
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        
        return SearchResponse(
            query=q,
            count=0,
            results=[],
            sources=sources_list,
            engine_used=None,
            error=f"Search failed: {str(e)}"
        )
