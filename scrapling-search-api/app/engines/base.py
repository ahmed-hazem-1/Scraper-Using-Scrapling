"""
Base search engine abstract class.

Defines the interface that all search engines must implement.
"""

from abc import ABC, abstractmethod
from typing import List
from app.models.schemas import SearchResult


class BaseEngine(ABC):
    """
    Abstract base class for search engines.
    
    All search engine implementations must inherit from this class
    and implement the required methods.
    """
    
    def __init__(self, settings):
        """
        Initialize the engine.
        
        Args:
            settings: Application settings instance
        """
        self.settings = settings
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the engine name.
        
        Returns:
            str: Human-readable engine name (e.g., "DuckDuckGo")
        """
        pass
    
    @abstractmethod
    def search(self, query: str, limit: int) -> List[SearchResult]:
        """
        Perform a search using this engine.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
        
        Returns:
            List[SearchResult]: List of search results
        
        Raises:
            Exception: If search fails or engine is unavailable
        """
        pass
    
    def is_rate_limited(self, results: List[SearchResult], status_code: int = None) -> bool:
        """
        Check if the engine appears to be rate limited.
        
        Override this method if your engine has specific rate limit detection.
        Default implementation checks for empty results with 202 status.
        
        Args:
            results: Search results returned
            status_code: HTTP status code (if applicable)
        
        Returns:
            bool: True if engine appears to be rate limited
        """
        # Common indicator: empty results with HTTP 202 Accepted
        if status_code == 202 and len(results) == 0:
            return True
        return False
