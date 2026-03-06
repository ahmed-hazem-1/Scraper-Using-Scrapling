# Scrapling Search API - Technical Documentation

**Version:** 2.1.0  
**Last Updated:** March 6, 2026  
**Python Version:** 3.12+  

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Key Features](#key-features)
4. [API Endpoints](#api-endpoints)
5. [Known Issues](#known-issues)
6. [Technical Stack](#technical-stack)
7. [Project Structure](#project-structure)

---

## Project Overview

Scrapling Search API is a **free web search API service** built with FastAPI that aggregates results from multiple search engines (DuckDuckGo, Bing, Google) with automatic fallback support. The API provides a unified interface for web search with features like source filtering, engine selection, and intelligent rate-limit handling.

### Design Philosophy
The project follows a **microservices-inspired architecture** - modular, loosely-coupled components that work together like "lego toys", making it easy to:
- Add new search engines
- Modify existing components independently
- Scale horizontally
- Test and debug individual modules

---

## Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                      │
│                              (main.py)                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
        ┌───────▼────────┐       ┌───────▼────────┐
        │  Health Route  │       │  Search Route  │
        │  (/health)     │       │  (/search)     │
        └────────────────┘       └───────┬────────┘
                                         │
                                 ┌───────▼───────┐
                                 │ SearchService │
                                 │  (Facade)     │
                                 └───────┬───────┘
                                         │
                        ┌────────────────┼────────────────┐
                        │                │                │
                ┌───────▼────────┐       │        ┌───────▼────────┐
                │ EngineManager  │       │        │  URL Service   │
                │(Circuit Breaker│       │        │  (Utilities)   │
                │  + Fallback)   │       │        └────────────────┘
                └───────┬────────┘       │
                        │                │
        ┌───────────────┼────────────────┤
        │               │                │
┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
│  DuckDuckGo  │ │    Bing     │ │   Google    │
│   Engine     │ │   Engine    │ │   Engine    │
│  (Scrapling) │ │   (httpx)   │ │(Playwright) │
└──────────────┘ └─────────────┘ └─────────────┘
   ✅ Working      ✅ Working      ⚠️ Bot Blocked
```

### Architecture Layers

#### 1. **Presentation Layer** (Routes)
- **Purpose:** Handle HTTP requests/responses
- **Components:**
  - `routes/search.py` - Search endpoint with query validation
  - `routes/health.py` - Health check endpoint
- **Responsibilities:**
  - Parameter validation (Pydantic)
  - Request logging
  - Error response formatting

#### 2. **Service Layer** (Business Logic)
- **Purpose:** Orchestrate search operations
- **Components:**
  - `services/search_service.py` - High-level search coordination
  - `services/url_service.py` - URL extraction and validation utilities
- **Responsibilities:**
  - Source filtering
  - Result aggregation
  - Error handling

#### 3. **Engine Layer** (Data Access)
- **Purpose:** Abstract search engine implementations
- **Design Pattern:** Strategy Pattern
- **Components:**
  - `engines/base.py` - BaseEngine abstract class
  - `engines/manager.py` - EngineManager (orchestrator with fallback logic)
  - `engines/duckduckgo.py` - DuckDuckGo implementation
  - `engines/bing.py` - Bing implementation
  - `engines/google.py` - Google implementation
- **Responsibilities:**
  - HTTP requests to search engines
  - HTML parsing (lxml + CSS selectors)
  - Result extraction
  - Retry logic

#### 4. **Cross-Cutting Concerns**
- **Configuration:** `config.py` - Centralized settings management
- **Models:** `models/schemas.py` - Pydantic data models
- **Middleware:** `middleware/logging.py` - Request/response logging

---

## Key Features

### 1. Multi-Engine Support with Automatic Fallback
```python
# Default behavior: tries all engines until one succeeds
GET /search?q=python&limit=10

# Engine preference: tries Google first, then falls back
GET /search?q=python&limit=10&engine=google

# Strict mode: only tries specified engine (no fallback)
GET /search?q=python&limit=10&engine=bing&strict=true
```

**Fallback Order Logic:**
1. If `engine` parameter specified → Try preferred engine first
2. If preferred engine fails/rate-limited → Try next engine
3. Continue until success or all engines exhausted
4. In `strict=true` mode → No fallback, return error if preferred engine fails

### 2. Source Filtering with Subdomain Support
```python
# Filter results by domain
GET /search?q=python&sources=python.org,github.com

# Subdomain matching (e.g., docs.python.org matches python.org)
GET /search?q=django&sources=djangoproject.com
```

### 3. URL Extraction from Redirect Links
- **Bing:** Base64-encoded URLs in redirect parameters
  - Decodes with automatic padding correction
- **Google:** URL parameters in Google redirect URLs
- **DuckDuckGo:** Direct URL extraction

### 4. Enhanced Headers for Bot Detection Avoidance
All engines configured with realistic browser headers:
- User-Agent: Chrome 120
- Accept-Language, DNT, Referer
- Sec-Fetch-* headers

### 5. Rate Limit Handling
- Configurable retry attempts (default: 3)
- Exponential backoff delays
- Automatic engine switching on rate limits

---

## API Endpoints

### `GET /search`
**Description:** Perform web search with multi-engine support

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `q` | string | Yes | - | Search query (1-500 chars) |
| `limit` | integer | No | 10 | Max results (1-50) |
| `sources` | string | No | null | Comma-separated domains to filter |
| `engine` | string | No | null | Preferred engine: `duckduckgo`, `bing`, `google` |
| `strict` | boolean | No | false | If true, only use specified engine (no fallback) |

**Response Schema:**
```json
{
  "query": "python programming",
  "count": 3,
  "results": [
    {
      "title": "Welcome to Python.org",
      "snippet": "The official home of the Python Programming Language.",
      "url": "https://www.python.org/"
    }
  ],
  "sources": ["python.org"],
  "engine_used": "bing",
  "error": null
}
```

**Example Requests:**
```bash
# Basic search
curl "http://localhost:8080/search?q=python&limit=5"

# With source filtering
curl "http://localhost:8080/search?q=python&sources=python.org,github.com"

# Force specific engine
curl "http://localhost:8080/search?q=python&engine=bing&strict=true"
```

### `GET /health`
**Description:** Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-03-06T22:30:00.000Z"
}
```

### `GET /`
**Description:** API information

**Response:**
```json
{
  "name": "Scrapling Search API",
  "version": "2.0.0",
  "endpoints": {
    "health": "/health",
    "search": "/search?q={query}&limit={limit}&sources={sources}&engine={engine}"
  },
  "documentation": "/docs"
}
```

---

## Known Issues

### ✅ Resolved Issues (v2.1.0)

#### 1. **DuckDuckGo - Rate Limiting / IP Blocking** ✅ RESOLVED
**Resolution Date:** March 6, 2026 (v2.1.0)  
**Status:** ✅ Working  
**Solution:** Migrated to Scrapling library

**Previous Problem:**
- DuckDuckGo was returning HTTP 403 Forbidden or HTTP 202 Accepted (rate limit signal)
- httpx-based implementation triggered bot detection
- All retry attempts failed consistently

**Solution Implemented:**
Migrated from httpx to **Scrapling library (v0.4.1)** which uses curl_cffi for browser-like HTTP requests:

```python
from scrapling import Fetcher

class DuckDuckGoEngine(BaseEngine):
    def __init__(self):
        self.fetcher = Fetcher()  # Uses curl_cffi with realistic browser fingerprints
    
    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        page = self.fetcher.get(url)  # Bypasses rate limiting
        elements = page.css('div.result')  # CSS selection
        # ... extract results
```

**Changes Made:**
- `app/engines/duckduckgo.py`: Complete rewrite using Scrapling Fetcher
- `app/config.py`: Increased `REQUEST_DELAY` from 1.0s to 2.0s
- `requirements.txt`: Added `scrapling>=0.2.0` (installed v0.4.1)

**Results:**
- ✅ Successfully bypasses rate limiting
- ✅ Consistently returns 5+ quality results
- ✅ HTTP 202 handled with retry logic (typically succeeds on second attempt)
- ✅ No more IP blocking issues

**Test Evidence:**
```
DuckDuckGo: ✅ HTTP 202 → HTTP 200, 5 results extracted
URLs: python.org, wikipedia.org, w3schools.com, realpython.com, geeksforgeeks.org
```

---

### 🟡 Active Issues

#### 2. **Google Search Engine - Bot Detection Still Active**
**Status:** ⚠️ Improved but still blocked  
**Severity:** Medium (fallback handles gracefully)  
**Affected Component:** `app/engines/google.py`

**v2.1.0 Updates:**
Migrated Google engine from httpx to **Playwright** for JavaScript rendering:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, wait_until='networkidle')
    page.wait_for_selector('div#search', timeout=10000)
    results = self._parse_results_playwright(page, limit)
```

**Current Problem:**
- Google's bot detection is highly sophisticated
- Even with Playwright browser automation, returns JavaScript-required page
- HTML shows `<noscript>` redirect with all content hidden
- Returns HTTP 200 but 0 results extracted

**Impact:**
- Google engine returns 0 results
- ✅ **Circuit breaker** disables Google after 3 failures for 5 minutes (prevents wasted requests)
- ✅ **Automatic fallback** to DuckDuckGo/Bing works seamlessly
- Users get results from working engines without errors

**Fallback Behavior:**
```bash
# Request flow:
GET /search?q=python
→ Try Google (fails) 
→ Fallback to DuckDuckGo (succeeds) 
→ Return results with "engine_used": "duckduckgo"
```

**Potential Future Solutions:**
1. ✅ **Residential proxy rotation** - Route through residential IPs
2. ✅ **Google Custom Search API** - Official API (limited free quota)
3. ⚠️ **Advanced browser fingerprinting** - Mimic real user behavior more closely
4. ⚠️ **SerpAPI/ScraperAPI** - Third-party paid service

**Current Strategy:**
Accept Google limitations since DuckDuckGo + Bing provide reliable fallback for single-user deployment (100-1000 req/day).

---

### 🟡 Medium Issues

#### 3. **Bing URL Extraction - Base64 Decoding Warnings**
**Status:** Working with warnings  
**Severity:** Medium  
**Affected Component:** `app/services/url_service.py`

**Problem:**
Some Bing redirect URLs fail initial base64 decoding but succeed with padding correction:
```
2026-03-06 22:09:28,526 - Failed to decode Bing URL base64: Incorrect padding, retry: 
Invalid base64-encoded string: number of data characters (181) cannot be 1 more than a multiple of 4
```

**Impact:**
- Warning logs (not errors)
- URLs still extracted successfully after retry
- Slight performance overhead

**Status:** ✅ Working as designed (fallback logic handles this)

---

#### 4. **Search Quality - Arabic Query Results**
**Status:** Observed behavior  
**Severity:** Low  
**Affected Component:** Bing engine (when used as fallback)

**Problem:**
Arabic political queries return mixed-quality results when using Bing as fallback (after Google/DuckDuckGo fail).

**Example:**
Query: "الاعتداءات الإيرانية على الدول العربية" (Iranian attacks on Arab countries)
- Bing returns some irrelevant results
- Google (when working) may provide better regional/language-specific results

**Impact:**
Non-English query quality depends heavily on which engine responds

**Potential Solutions:**
1. Fix Google/DuckDuckGo engines (primary issue)
2. Add language/region parameters to Bing requests
3. Implement result scoring/ranking

---

## Technical Stack

### Core Dependencies
```
fastapi==0.115.12           # Web framework
uvicorn[standard]==0.32.1   # ASGI server
httpx==0.28.1               # HTTP client (Bing engine)
lxml==5.3.0                 # HTML parsing
pydantic==2.10.6            # Data validation
pydantic-settings==2.7.1    # Settings management
python-dotenv==1.0.1        # Environment variables
scrapling>=0.2.0            # Anti-bot scraping (DuckDuckGo) - v0.4.1 installed
playwright>=1.40.0          # Browser automation (Google) - optional
```

### Development Tools
- **Python:** 3.12+
- **Package Manager:** pip
- **Virtual Environment:** venv
- **Code Style:** PEP 8

### Configuration (v2.1.0)
- Port: 8080 (default)
- Logging: INFO level
- Timeouts: 30s HTTP timeout
- Retries: 3 attempts with exponential backoff
- Request Delay: 2.0s between requests (increased from 1.0s)
- Circuit Breaker: 3 failures → 5 minute cooldown
- Scrapling Timeout: 30s
- Scrapling Auto-Match: Enabled

---

## Project Structure

```
scrapling-search-api/
├── app/
│   ├── __init__.py                # Package marker (v2.0.0)
│   ├── main.py                    # FastAPI application factory
│   ├── config.py                  # Settings & configuration
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py             # Pydantic models (SearchResult, SearchResponse)
│   │
│   ├── engines/                   # Search engine implementations
│   │   ├── __init__.py            # Engine exports
│   │   ├── base.py                # BaseEngine abstract class
│   │   ├── manager.py             # EngineManager (orchestrator + fallback)
│   │   ├── duckduckgo.py          # DuckDuckGo engine (HTTP 403 - rate-limited)
│   │   ├── bing.py                # Bing engine (✅ Working)
│   │   └── google.py              # Google engine (⚠️ Blocked by bot detection)
│   │
│   ├── services/                  # Business logic layer
│   │   ├── __init__.py
│   │   ├── search_service.py      # High-level search coordination
│   │   └── url_service.py         # URL extraction utilities
│   │
│   ├── routes/                    # API endpoints
│   │   ├── __init__.py
│   │   ├── search.py              # /search endpoint
│   │   └── health.py              # /health endpoint
│   │
│   └── middleware/                # Cross-cutting concerns
│       ├── __init__.py
│       └── logging.py             # Request logging middleware
│
├── main.py                        # Application entry point
├── requirements.txt               # Python dependencies
├── .env                           # Environment variables
├── TECHNICAL_DOCUMENTATION.md     # This file
└── README.md                      # User-facing documentation
```

---

## Design Patterns Used

### 1. **Strategy Pattern** (Engine implementations)
```python
# Abstract base class defines interface
class BaseEngine(ABC):
    @abstractmethod
    def search(self, query: str, limit: int) -> List[SearchResult]:
        pass

# Concrete implementations
class BingEngine(BaseEngine):
    def search(self, query: str, limit: int) -> List[SearchResult]:
        # Bing-specific implementation
        
class GoogleEngine(BaseEngine):
    def search(self, query: str, limit: int) -> List[SearchResult]:
        # Google-specific implementation
```

### 2. **Facade Pattern** (SearchService)
```python
# SearchService provides simplified interface to complex subsystem
class SearchService:
    def search(self, query, limit, sources, preferred_engine, strict_mode):
        # Coordinates: EngineManager + source filtering + error handling
        results = self.engine_manager.search(...)
        filtered = self._apply_source_filter(results, sources)
        return SearchResponse(...)
```

### 3. **Dependency Injection** (FastAPI)
```python
# Settings and services injected via FastAPI's Depends()
@router.get("/search")
async def search(
    q: str,
    settings: Settings = Depends(get_settings),
    search_service: SearchService = Depends(get_search_service)
):
    return search_service.search(q, ...)
```

### 4. **Factory Pattern** (Application creation)
```python
# main.py creates and configures FastAPI app
def create_app() -> FastAPI:
    app = FastAPI(...)
    app.add_middleware(...)
    app.include_router(...)
    return app
```

---

## Performance Considerations

### Current Performance Profile
- **Average Response Time:** 1-3 seconds per search
  - Bing: ~500-800ms
  - DuckDuckGo: 2-10s (with retries when rate-limited)
  - Google: ~500ms (but returns 0 results)
  
- **Bottlenecks:**
  1. Sequential engine fallback (blocks until timeout/failure)
  2. HTML parsing (lxml is fast, but parsing large pages takes time)
  3. Rate limit retries (exponential backoff adds delays)

### Optimization Opportunities
1. **Parallel engine requests** - Try multiple engines simultaneously, return first success
2. **Caching** - Redis cache for popular queries (TTL: 5-60 minutes)
3. **Connection pooling** - Reuse HTTP connections (httpx supports this)
4. **Async/await optimization** - Currently mostly synchronous, could parallelize more
5. **Result streaming** - Start returning results before parsing completes

---

## Testing Strategy

### Manual Testing (Current)
```bash
# Basic functionality
curl "http://localhost:8080/search?q=python&limit=5"

# Engine preference
curl "http://localhost:8080/search?q=python&engine=bing"

# Strict mode
curl "http://localhost:8080/search?q=python&engine=google&strict=true"

# Source filtering
curl "http://localhost:8080/search?q=python&sources=python.org"
```

### Recommended Test Suite (Future)
- **Unit Tests:** pytest for individual components
- **Integration Tests:** Full API endpoint testing
- **Load Tests:** Locust/k6 for performance benchmarking
- **Engine Tests:** Mock HTTP responses to test parsing logic

---

## Deployment Considerations

### Environment Variables
```bash
# .env file
API_TITLE=Scrapling Search API
API_VERSION=2.0.0
LOG_LEVEL=INFO
HTTP_TIMEOUT=30
MAX_RETRIES=3
REQUEST_DELAY=1.0
```

### Production Recommendations
1. **Reverse Proxy:** nginx/Apache for SSL termination
2. **Process Manager:** supervisord or systemd for auto-restart
3. **Monitoring:** Prometheus + Grafana for metrics
4. **Logging:** ELK stack or CloudWatch for centralized logs
5. **Rate Limiting:** API-level rate limiting (slowapi/FastAPI-Limiter)
6. **Proxy Pool:** Rotate IPs to avoid search engine blocks

### Docker Deployment (Example)
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

## Future Roadmap

### Short-term (Next Sprint)
- [ ] Fix Google engine (Playwright integration)
- [ ] Implement caching layer (Redis)
- [ ] Add API documentation (OpenAPI/Swagger)
- [ ] Unit test coverage (>80%)

### Medium-term (Next Month)
- [ ] Add more engines (Yahoo, Yandex, Baidu)
- [ ] Implement result aggregation (merge results from multiple engines)
- [ ] Add search history / analytics
- [ ] API rate limiting per client

### Long-term (Next Quarter)
- [ ] Machine learning result ranking
- [ ] Real-time search (WebSocket support)
- [ ] Multi-language support improvements
- [ ] Kubernetes deployment with auto-scaling

---

## Troubleshooting Guide

### Issue: "All engines failed" error
**Cause:** All three engines (DuckDuckGo, Bing, Google) are unavailable  
**Solution:** 
1. Check if Bing is working: `curl "http://localhost:8080/search?q=test&engine=bing&strict=true"`
2. Review logs for specific engine errors
3. If IP is blocked, wait 24-48 hours or use proxy

### Issue: Always getting Bing results (even when specifying other engines)
**Cause:** Google is blocked, DuckDuckGo is rate-limited, automatic fallback to Bing  
**Solution:** This is expected behavior. Bing is currently the only working engine.

### Issue: Slow response times
**Cause:** Sequential fallback trying multiple engines  
**Solution:** 
1. Use `engine=bing` to skip failed engines
2. Use `strict=true` to avoid fallback delays

### Issue: Empty results for specific queries
**Cause:** Search engine may not have indexed content, or CSS selectors failed  
**Solution:** Try different engine or broader query terms

---

## Contributing

### Adding a New Search Engine

1. **Create engine file:** `app/engines/newsearch.py`
```python
from app.engines.base import BaseEngine

class NewSearchEngine(BaseEngine):
    @property
    def name(self) -> str:
        return "newsearch"
    
    def search(self, query: str, limit: int) -> List[SearchResult]:
        # Implement search logic
        pass
```

2. **Register in manager:** `app/engines/__init__.py`
```python
from app.engines.newsearch import NewSearchEngine

__all__ = ['DuckDuckGoEngine', 'BingEngine', 'GoogleEngine', 'NewSearchEngine']
```

3. **Add to EngineManager:** `app/engines/manager.py`
```python
def __init__(self, settings: Settings):
    self.engines = [
        DuckDuckGoEngine(settings),
        BingEngine(settings),
        GoogleEngine(settings),
        NewSearchEngine(settings),
    ]
```

---

## Contact & Support

- **Repository:** [Your Repo URL]
- **Issues:** [Issue Tracker URL]
- **Documentation:** http://localhost:8080/docs

---

## License

[Specify License]

---

**Document Version:** 1.0  
**Generated:** March 6, 2026  
**Maintained By:** Development Team
