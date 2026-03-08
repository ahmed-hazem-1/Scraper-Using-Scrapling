"""
Pydantic models for request validation and response serialization.

These models provide:
- Automatic validation
- Type safety
- API documentation
- JSON serialization
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl


class SearchResult(BaseModel):
    """
    Individual search result item.
    
    Attributes:
        title: Page title
        snippet: Brief description/excerpt from the page
        url: Full URL to the page
        content: Full text content extracted from result (more comprehensive than snippet)
        date: Date string if found in the result (format varies by source)
    """
    title: str = Field(..., description="Page title")
    snippet: str = Field(..., description="Brief description or excerpt")
    url: str = Field(..., description="Full URL to the result page")
    content: Optional[str] = Field(None, description="Full text content from search result")
    date: Optional[str] = Field(None, description="Date string extracted from result if available")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Python Programming Language",
                "snippet": "Python is a versatile and easy-to-learn language...",
                "url": "https://www.python.org/",
                "content": "Python is a versatile and easy-to-learn programming language. Released in 1991, it emphasizes code readability...",
                "date": "Feb. 3, 2026"
            }
        }


class SearchResponse(BaseModel):
    """
    Search API response model.
    
    Attributes:
        query: The search query string
        count: Number of results returned
        results: List of search results
        sources: Optional list of source domains to filter by
        engine_used: Name of the search engine that provided results
        error: Optional error message if search failed
    """
    query: str = Field(..., description="The search query")
    count: int = Field(..., description="Number of results returned", ge=0)
    results: List[SearchResult] = Field(default_factory=list, description="List of search results")
    sources: Optional[List[str]] = Field(None, description="Source domains filter (e.g., ['python.org', 'github.com'])")
    engine_used: Optional[str] = Field(None, description="Search engine that provided results (e.g., 'duckduckgo', 'bing', 'google')")
    error: Optional[str] = Field(None, description="Error message if search failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "python programming",
                "count": 3,
                "results": [
                    {
                        "title": "Python.org",
                        "snippet": "Official Python website...",
                        "url": "https://www.python.org/"
                    }
                ],
                "sources": ["python.org", "github.com"],
                "engine_used": "duckduckgo"
            }
        }


class HealthResponse(BaseModel):
    """
    Health check response model.
    
    Attributes:
        status: Service status ("ok" or "error")
        timestamp: Current server timestamp
        version: API version
    """
    status: str = Field(..., description="Service status")
    timestamp: Optional[datetime] = Field(None, description="Current server time")
    version: Optional[str] = Field(None, description="API version")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "timestamp": "2026-03-06T20:00:00",
                "version": "2.0.0"
            }
        }


class APIInfo(BaseModel):
    """
    API information response for root endpoint.
    
    Attributes:
        name: API name
        version: API version
        endpoints: Available endpoints
        documentation: Link to API documentation
    """
    name: str = Field(..., description="API name")
    version: str = Field(..., description="API version")
    endpoints: dict = Field(..., description="Available endpoints")
    documentation: str = Field(..., description="Documentation URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Scrapling Search API",
                "version": "2.0.0",
                "endpoints": {
                    "health": "/health",
                    "search": "/search?q={query}&limit={limit}"
                },
                "documentation": "/docs"
            }
        }


class ErrorResponse(BaseModel):
    """
    Error response model.
    
    Attributes:
        error: Error message
        detail: Optional detailed error information
    """
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Search failed",
                "detail": "Connection timeout"
            }
        }
