"""
Health check routes.

This module provides endpoints for monitoring service health.
"""

from datetime import datetime
from fastapi import APIRouter, Depends
from app.models.schemas import HealthResponse
from app.config import Settings, get_settings, get_logger

logger = get_logger(__name__)

# Create router
router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check if the service is running and healthy"
)
async def health_check(
    settings: Settings = Depends(get_settings)
) -> HealthResponse:
    """
    Health check endpoint for monitoring.
    
    Returns service status, timestamp, and version information.
    This endpoint can be used by:
    - Load balancers for health checks
    - Monitoring systems for uptime tracking
    - DevOps tools for deployment verification
    
    Returns:
        HealthResponse: Service health status
    """
    logger.debug("Health check requested")
    
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow(),
        version=settings.api_version
    )
