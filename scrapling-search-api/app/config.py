"""
Configuration module for Scrapling Search API.

Centralizes all application settings, environment variables,
and configuration constants.
"""

import os
import logging
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    These can be overridden by creating a .env file or setting
    environment variables directly.
    """
    
    # Server Configuration
    port: int = 8080
    host: str = "0.0.0.0"
    
    # Search Configuration
    max_results: int = 10
    max_search_limit: int = 50
    default_search_limit: int = 10
    
    # HTTP Client Configuration
    http_timeout: float = 30.0
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    request_delay: float = 2.0  # Delay between requests to avoid rate limiting
    
    # DuckDuckGo Configuration
    duckduckgo_url: str = "https://html.duckduckgo.com/html/"
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    
    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # API Metadata
    api_title: str = "Scrapling Search API"
    api_description: str = "Free web search API using DuckDuckGo"
    api_version: str = "2.1.0"
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings (cached singleton).
    
    Returns:
        Settings: Application settings instance
    """
    return Settings()


def configure_logging(settings: Optional[Settings] = None) -> None:
    """
    Configure application logging.
    
    Args:
        settings: Optional settings instance (will use default if not provided)
    """
    if settings is None:
        settings = get_settings()
    
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format=settings.log_format
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Name of the logger (typically __name__)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)
