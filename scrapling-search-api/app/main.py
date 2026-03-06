"""
Main FastAPI application factory.

This module creates and configures the FastAPI application instance,
including middleware, routes, and CORS settings.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings, configure_logging, get_logger
from app.middleware.logging import setup_logging_middleware
from app.routes import health, search

# Initialize settings and logging
settings = get_settings()
configure_logging(settings)
logger = get_logger(__name__)


def create_app() -> FastAPI:
    """
    Application factory for creating FastAPI instances.
    
    This function:
    1. Creates a FastAPI application
    2. Configures CORS middleware
    3. Adds custom logging middleware
    4. Registers route handlers
    
    Returns:
        FastAPI: Configured application instance
    """
    logger.info(f"Creating FastAPI application - {settings.api_title} v{settings.api_version}")
    
    # Create FastAPI app with metadata
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Configure CORS middleware (allow all origins for public API)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify exact origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS middleware configured (allow all origins)")
    
    # Add custom logging middleware
    setup_logging_middleware(app)
    
    # Register route handlers
    app.include_router(health.router)
    logger.info("Health check routes registered")
    
    app.include_router(search.router)
    logger.info("Search routes registered")
    
    logger.info("FastAPI application created successfully")
    
    return app


# Create the application instance
app = create_app()


@app.on_event("startup")
async def startup_event():
    """
    Startup event handler.
    
    Called when the application starts. Can be used for:
    - Database connection initialization
    - Cache warming
    - Background task startup
    """
    logger.info("=" * 60)
    logger.info(f"Starting {settings.api_title} v{settings.api_version}")
    logger.info(f"Server: {settings.host}:{settings.port}")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"DuckDuckGo URL: {settings.duckduckgo_url}")
    logger.info(f"Max retries: {settings.max_retries}")
    logger.info(f"Documentation: http://{settings.host}:{settings.port}/docs")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event handler.
    
    Called when the application shuts down. Can be used for:
    - Closing database connections
    - Cleaning up resources
    - Final logging
    """
    logger.info("Shutting down application...")
    logger.info(f"{settings.api_title} stopped")


# For running with uvicorn directly
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,  # Enable auto-reload for development
        log_level=settings.log_level.lower()
    )
