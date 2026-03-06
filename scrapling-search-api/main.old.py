import os
import time
import logging
from typing import Optional, List, Dict
from urllib.parse import quote_plus, parse_qs, urlparse, unquote

from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import httpx
from lxml import html as lxml_html

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Scrapling Search API",
    description="Free web search API using Scrapling + DuckDuckGo",
    version="1.0.0"
)

# Add CORS middleware (allow all origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Request started: {request.method} {request.url}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"Request completed: {request.method} {request.url} - "
        f"Status: {response.status_code} - Time: {process_time:.2f}s"
    )
    return response


def extract_actual_url(ddg_url: str) -> str:
    """
    Extract the actual URL from DuckDuckGo's redirect URL.
    
    Args:
        ddg_url: DuckDuckGo redirect URL (e.g., //duckduckgo.com/l/?uddg=...)
        
    Returns:
        The actual target URL
    """
    try:
        # Add https: if URL starts with //
        if ddg_url.startswith('//'):
            ddg_url = 'https:' + ddg_url
        
        # Parse the URL and extract the 'uddg' parameter
        parsed = urlparse(ddg_url)
        params = parse_qs(parsed.query)
        
        if 'uddg' in params:
            actual_url = unquote(params['uddg'][0])
            return actual_url
        
        return ddg_url
    except Exception as e:
        logger.warning(f"Failed to extract URL from {ddg_url}: {e}")
        return ddg_url


def scrape_duckduckgo(query: str, max_results: int = 10, max_retries: int = 3) -> List[Dict[str, str]]:
    """
    Scrape DuckDuckGo HTML version for search results.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
        max_retries: Maximum number of retry attempts
        
    Returns:
        List of search result dictionaries with title, snippet, and url
    """
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    results = []
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries}: Fetching {url}")
            
            # Use httpx to fetch HTML
            with httpx.Client(timeout=30.0) as client:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                response = client.get(url, headers=headers, follow_redirects=True)
                response.raise_for_status()
                
                # Parse HTML with lxml
                tree = lxml_html.fromstring(response.text)
            
            # Find all result containers
            result_elements = tree.cssselect('.result')
            logger.info(f"Found {len(result_elements)} result elements")
            
            for idx, result in enumerate(result_elements):
                if len(results) >= max_results:
                    break
                    
                try:
                    # Extract title
                    title_elem = result.cssselect('.result__title')
                    title = title_elem[0].text_content().strip() if title_elem else ""
                    
                    # Extract snippet
                    snippet_elem = result.cssselect('.result__snippet')
                    snippet = snippet_elem[0].text_content().strip() if snippet_elem else ""
                    
                    # Extract URL from the result__a link (title link)
                    result_url = ""
                    title_link = result.cssselect('.result__a')
                    if title_link:
                        ddg_url = title_link[0].get('href', '')
                        result_url = extract_actual_url(ddg_url)
                    
                    # Strip whitespace
                    title = title.strip()
                    snippet = snippet.strip()
                    result_url = result_url.strip()
                    
                    # Only add results with valid URLs
                    if result_url and result_url.startswith('http'):
                        results.append({
                            "title": title,
                            "snippet": snippet,
                            "url": result_url
                        })
                        logger.debug(f"Extracted result {len(results)}: {title[:50]}...")
                    
                except Exception as e:
                    logger.warning(f"Failed to parse result {idx}: {str(e)}")
                    continue
            
            # If we got results, break the retry loop
            if results:
                logger.info(f"Successfully extracted {len(results)} results")
                break
                
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # Exponential backoff
                logger.info(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                logger.error(f"All {max_retries} attempts failed")
                raise
    
    return results


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok"}


@app.get("/search")
async def search(
    q: str = Query(..., description="Search query", min_length=1),
    limit: Optional[int] = Query(
        default=10,
        description="Maximum number of results",
        ge=1,
        le=50
    )
):
    """
    Search endpoint using DuckDuckGo via Scrapling.
    
    Args:
        q: Search query string (required)
        limit: Maximum number of results to return (optional, default=10, max=50)
        
    Returns:
        JSON response with query, count, and results array
    """
    try:
        logger.info(f"Search request: query='{q}', limit={limit}")
        
        # Scrape DuckDuckGo for results
        results = scrape_duckduckgo(query=q, max_results=limit)
        
        response = {
            "query": q,
            "count": len(results),
            "results": results
        }
        
        logger.info(f"Search completed: {len(results)} results returned")
        return response
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}", exc_info=True)
        
        # Return empty results with error message
        return JSONResponse(
            status_code=200,
            content={
                "query": q,
                "count": 0,
                "results": [],
                "error": f"Search failed: {str(e)}"
            }
        )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Scrapling Search API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "search": "/search?q={query}&limit={limit}"
        },
        "documentation": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
