"""
Logging middleware for request/response tracking.

This module provides middleware for:
- Logging incoming requests
- Logging response details
- Measuring request processing time
- Error tracking
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.
    
    This middleware logs:
    - Request method and URL
    - Response status code
    - Processing time
    - Errors (if any)
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and log details.
        
        Args:
            request: Incoming request
            call_next: Next middleware/route handler
        
        Returns:
            Response: HTTP response
        """
        # Record start time
        start_time = time.time()
        
        # Log request start
        logger.info(f"Request started: {request.method} {request.url}")
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log successful response
            logger.info(
                f"Request completed: {request.method} {request.url} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.2f}s"
            )
            
            return response
            
        except Exception as e:
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url} - "
                f"Error: {str(e)} - "
                f"Time: {process_time:.2f}s",
                exc_info=True
            )
            
            # Re-raise the exception
            raise


def setup_logging_middleware(app):
    """
    Add logging middleware to the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(RequestLoggingMiddleware)
    logger.info("Request logging middleware configured")
