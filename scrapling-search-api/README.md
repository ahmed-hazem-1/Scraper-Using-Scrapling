# Scrapling Search API

A free web search API with **multi-engine support** and automatic fallback. Built with FastAPI, Scrapling, Playwright, and lxml for fast, reliable web searches without API keys.

**✨ v2.1.0 Update:** Now using Scrapling library to bypass bot detection and rate limiting!

## Features

- 🚀 **FastAPI-based REST API** - Modern, fast, with automatic API docs
- 🔍 **Multi-Engine Support** - DuckDuckGo, Bing, and Google with automatic fallback
- ⚡ **Automatic Failover** - If one engine is rate-limited, tries the next
- 🛡️ **Anti-Bot Protection** (v2.1.0) - Scrapling library bypasses rate limiting and bot detection
- 🌐 **Browser Automation** (v2.1.0) - Playwright integration for JavaScript-heavy sites
- 🔄 **Circuit Breaker Pattern** (v2.1.0) - Disables failing engines temporarily to optimize performance
- 🎯 **Source Filtering** - Filter results by domain (e.g., only stackoverflow.com)
- 📦 **Lightweight** - Minimal dependencies, fast startup
- 🏗️ **Modular Architecture** - Clean, scalable, "like lego toys"
- 🐳 **Docker Support** - Ready for containerized deployment
- ☁️ **Google Cloud Run Ready** - Production-ready configuration
- 📊 **Request Logging** - Comprehensive logging for debugging
- 🌐 **CORS Enabled** - Ready for web applications

## Architecture

The API uses a **modular, microservices-style architecture** for scalability and maintainability:

```
scrapling-search-api/
├── app/
│   ├── __init__.py          # Application factory
│   ├── main.py              # FastAPI app creation
│   ├── config.py            # Settings and configuration
│   ├── engines/             # Search engine implementations
│   │   ├── __init__.py      # Engine exports
│   │   ├── base.py          # BaseEngine abstract class
│   │   ├── duckduckgo.py    # DuckDuckGo implementation
│   │   ├── bing.py          # Bing implementation
│   │   ├── google.py        # Google implementation
│   │   └── manager.py       # Engine orchestration & fallback
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   ├── services/
│   │   ├── search_service.py  # High-level search service
│   │   └── url_service.py     # URL utilities
│   ├── middleware/
│   │   └── logging.py       # Request logging
│   └── routes/
│       ├── health.py        # Health check endpoint
│       └── search.py        # Search endpoints
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration
└── README.md               # This file
```

### Engine Architecture

Each search engine is implemented as a separate, pluggable module:

- **BaseEngine** (abstract): Defines the interface all engines must implement
- **DuckDuckGoEngine**: Primary engine using DuckDuckGo HTML
- **BingEngine**: Secondary engine using Bing HTML
- **GoogleEngine**: Tertiary engine using Google HTML
- **EngineManager**: Orchestrates engines with automatic fallback logic

When a search is performed:
1. Try preferred engine first (or DuckDuckGo by default)
2. If engine fails or is rate-limited, try next engine
3. Return results from first successful engine
4. Include `engine_used` in response to show which engine provided results

## API Endpoints

### Root
- **GET** `/`
- Returns API information and available endpoints

### Health Check
- **GET** `/health`
- Returns: `{"status": "ok", "timestamp": "...", "version": "2.1.0"}`

### Search
- **GET** `/search?q={query}&limit={limit}&sources={sources}&engine={engine}`
- Parameters:
  - `q` (required): Search query string
  - `limit` (optional): Maximum results (default: 10, max: 50)
  - `sources` (optional): Comma-separated domain filter (e.g., `python.org,github.com`)
  - `engine` (optional): Preferred search engine (`duckduckgo`, `bing`, or `google`)
- Returns:
  ```json
  {
    "query": "python programming",
    "count": 5,
    "results": [
      {
        "title": "Result Title",
        "snippet": "Description or snippet text...",
        "url": "https://example.com"
      }
    ],
    "sources": ["python.org"],
    "engine_used": "duckduckgo",
    "error": null
  }
  ```

### Interactive Documentation
- **GET** `/docs` - Swagger UI for testing endpoints
- **GET** `/redoc` - ReDoc alternative documentation

## Local Setup

### Prerequisites
- Python 3.11+
- pip

### Installation

1. **Navigate to project directory:**
   ```bash
   cd scrapling-search-api
   ```

2. **Create virtual environment (recommended):**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file (optional):**
   ```bash
   copy .env.example .env  # Windows
   cp .env.example .env    # Linux/Mac
   ```

### Running Locally

Start the development server:
```bash
uvicorn main:app --reload --port 8080
```

The API will be available at `http://localhost:8080`

Access the interactive API documentation at `http://localhost:8080/docs`

## Testing Examples

### Health Check
```bash
curl http://localhost:8080/health
```

**Response:**
```json
{"status": "ok", "timestamp": "2024-01-01T12:00:00", "version": "2.1.0"}
```

### Basic Search
```bash
curl "http://localhost:8080/search?q=python+programming&limit=5"
```

### Search with Source Filtering
Filter results to only show results from specific domains:
```bash
curl "http://localhost:8080/search?q=python+tutorial&sources=python.org,realpython.com"
```

### Search with Preferred Engine
Specify which search engine to use:
```bash
curl "http://localhost:8080/search?q=javascript&limit=5&engine=bing"
```

### Combined Filters
```bash
curl "http://localhost:8080/search?q=fastapi+tutorial&limit=10&sources=fastapi.tiangolo.com&engine=duckduckgo"
```

### PowerShell Examples (Windows)
```powershell
# Health check
Invoke-RestMethod -Uri "http://localhost:8080/health"

# Basic search
Invoke-RestMethod -Uri "http://localhost:8080/search?q=python&limit=5"

# Search with source filtering
Invoke-RestMethod -Uri "http://localhost:8080/search?q=python&sources=python.org"

# Search with specific engine
Invoke-RestMethod -Uri "http://localhost:8080/search?q=react&engine=google"

# Get formatted JSON output
Invoke-RestMethod -Uri "http://localhost:8080/search?q=python&limit=3" | ConvertTo-Json -Depth 3
```

### Example Response
```json
{
  "query": "python programming",
  "count": 3,
  "results": [
    {
      "title": "Welcome to Python.org",
      "snippet": "The official home of the Python Programming Language...",
      "url": "https://www.python.org/"
    },
    {
      "title": "Python Tutorial",
      "snippet": "Learn Python programming with our comprehensive tutorial...",
      "url": "https://docs.python.org/3/tutorial/"
    }
  ],
  "sources": null,
  "engine_used": "duckduckgo",
  "error": null
}
```

## Docker

### Build Docker Image

Build the Docker image:
```bash
docker build -t scrapling-api .
```

### Run Docker Container Locally

Run the container:
```bash
docker run -p 8080:8080 scrapling-api
```

Run with environment variables:
```bash
docker run -p 8080:8080 -e PORT=8080 -e MAX_RESULTS=10 scrapling-api
```

Run in detached mode:
```bash
docker run -d -p 8080:8080 --name search-api scrapling-api
```

Check logs:
```bash
docker logs search-api
```

Stop container:
```bash
docker stop search-api
```

## Google Cloud Run Deployment

### Prerequisites
- Google Cloud account
- gcloud CLI installed and configured
- Project ID ready

### Deploy to Cloud Run

1. **Set your project ID:**
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Build and deploy in one command:**
   ```bash
   gcloud run deploy scrapling-search-api \
     --source . \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --port 8080 \
     --memory 2Gi \
     --cpu 2 \
     --timeout 300 \
     --max-instances 10
   ```

3. **Or build with Cloud Build and deploy:**
   ```bash
   # Build image
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/scrapling-search-api
   
   # Deploy to Cloud Run
   gcloud run deploy scrapling-search-api \
     --image gcr.io/YOUR_PROJECT_ID/scrapling-search-api \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --port 8080 \
     --memory 2Gi \
     --cpu 2
   ```

4. **Get the service URL:**
   ```bash
   gcloud run services describe scrapling-search-api --region us-central1 --format 'value(status.url)'
   ```

### Test Cloud Run Deployment
```bash
curl "https://YOUR-SERVICE-URL/health"
curl "https://YOUR-SERVICE-URL/search?q=test&limit=5"
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8080` | Server port |
| `MAX_RESULTS` | `10` | Default maximum results |

## Technical Details

### Multi-Engine Architecture
The API uses a **Strategy Pattern** with multiple search engines:

#### DuckDuckGo Engine
- **CSS Selectors**: `.result`, `.result__title`, `.result__snippet`, `.result__a`
- **URL Extraction**: Extracts actual URLs from DuckDuckGo redirect links (`uddg` parameter)
- **Priority**: Primary (tried first by default)

#### Bing Engine
- **CSS Selectors**: `.b_algo`, `h2 a`, `.b_caption p`
- **URL Format**: Bing redirect URLs
- **Priority**: Secondary (fallback when DuckDuckGo fails)

#### Google Engine
- **CSS Selectors**: `div.g`, `h3`, `.VwiC3b`
- **Special Features**: Enhanced headers to avoid bot detection
- **Priority**: Tertiary (last fallback)

### Scraping Strategy
- Uses **httpx** for fast HTTP requests (no browser automation)
- Uses **lxml** for efficient HTML parsing with CSS selectors
- Each engine has independent parsing logic
- Implements retry logic with exponential backoff (max 3 attempts)
- Automatic fallback between engines on failure

### Source Filtering
- Filter results by domain name (e.g., `sources=python.org,github.com`)
- Supports subdomain matching: `wikipedia.org` matches `en.wikipedia.org`
- Applied after search results are retrieved
- Works with all search engines

### Engine Fallback Logic
1. Try preferred engine (or DuckDuckGo by default)
2. If engine returns no results or is rate-limited, try next engine
3. Engines are tried in order: DuckDuckGo → Bing → Google
4. Return results from first successful engine
5. Include `engine_used` field in response

### Error Handling
- Graceful degradation with automatic engine fallback
- Empty results with error message if all engines fail
- Per-engine retry logic for transient failures
- Comprehensive logging for debugging
- Request-level error isolation

## Development

### Project Dependencies
- **FastAPI**: Modern, fast web framework with automatic API docs
- **Uvicorn**: Lightning-fast ASGI server
- **httpx**: HTTP client for Bing engine
- **scrapling**: Anti-bot scraping library using curl_cffi (v0.4.1) - v2.1.0
- **playwright**: Browser automation for JavaScript rendering (optional) - v2.1.0
- **lxml**: Fast HTML/XML parser with CSS selector support
- **pydantic** & **pydantic-settings**: Data validation and settings management

### Code Architecture

#### Modular Design
The codebase follows **microservices principles** for scalability:

- **app/config.py**: Centralized configuration with environment variable support
- **app/models/schemas.py**: Pydantic models for type safety and validation
- **app/engines/**: Pluggable search engine implementations
  - Each engine is independent and swappable
  - Implements `BaseEngine` abstract class
  - Manager orchestrates multi-engine fallback
- **app/services/**: Business logic layer
  - `SearchService`: High-level search orchestration
  - `url_service`: URL utilities (extraction, validation, domain matching)
- **app/middleware/**: Request processing middleware
- **app/routes/**: API endpoint definitions

#### Design Patterns
- **Strategy Pattern**: Pluggable search engines
- **Factory Pattern**: Application creation with dependency injection
- **Repository Pattern**: Service layer abstracts engine details
- **Dependency Injection**: FastAPI's `Depends()` for clean separation

#### Adding a New Search Engine
1. Create new file in `app/engines/` (e.g., `yandex.py`)
2. Inherit from `BaseEngine` abstract class
3. Implement `name` property and `search()` method
4. Add to `EngineManager` in `app/engines/manager.py`
5. Engine automatically available with fallback support

Example:
```python
# app/engines/yandex.py
from app.engines.base import BaseEngine

class YandexEngine(BaseEngine):
    @property
    def name(self) -> str:
        return "yandex"
    
    def search(self, query: str, limit: int) -> List[SearchResult]:
        # Implement Yandex-specific scraping
        pass
```

## Troubleshooting

### Common Issues

**Issue: No results returned**
- Check `engine_used` field to see which engine provided results
- All engines might be rate-limited - wait and try again
- Check logs for detailed error messages: `docker logs search-api`
- Try different engine: `?engine=bing` or `?engine=google`

**Issue: Rate limiting**
- API automatically falls back to other engines
- Implement caching for frequently searched queries
- Add delays between requests in client code
- Consider using proxy rotation for high-volume deployments

**Issue: Module not found errors**
```bash
pip install -r requirements.txt
```

**Issue: Permission denied on Linux**
```bash
sudo apt-get install libxml2-dev libxslt-dev python3-dev
pip install lxml
```

**Issue: Docker build fails**
- Ensure you have enough disk space
- Try building with `--no-cache` flag:
  ```bash
  docker build --no-cache -t scrapling-api .
  ```

**Issue: Source filtering returns no results**
- Check if specified domains actually appear in search results
- Try broader domain matching (e.g., `github.com` matches `gist.github.com`)
- Verify domain spelling
- Test without source filter first to see available domains

## Performance Considerations

- Each search request takes 2-5 seconds (depends on network)
- Recommended: 2GB memory, 2 CPU cores for production
- Consider implementing caching for frequently searched queries
- Rate limiting recommended for public deployments

## Security Notes

- CORS is enabled for all origins (configure for production)
- No API key required
- Consider implementing rate limiting
- Monitor for abuse in production environments

## License

MIT License - feel free to use for any purpose.

## Contributing

Contributions welcome! Please feel free to submit issues or pull requests.

## Support

For issues or questions:
- Check logs: `docker logs search-api`
- Review scraping function in `main.py`
- Test locally before deploying

## Roadmap

### ✅ Completed
- [x] Multi-engine support (DuckDuckGo, Bing, Google)
- [x] Automatic fallback between engines
- [x] Source filtering by domain
- [x] Modular, scalable architecture
- [x] Comprehensive error handling
- [x] Interactive API documentation
- [x] Docker support
- [x] Cloud Run ready
- [x] **v2.1.0:** Scrapling integration for anti-bot protection
- [x] **v2.1.0:** Playwright integration for JavaScript rendering
- [x] **v2.1.0:** Circuit breaker pattern for failing engines
- [x] **v2.1.0:** DuckDuckGo rate limiting resolved

### 🚀 Future Enhancements
- [ ] Caching layer (Redis) for performance
- [ ] Rate limiting per client
- [ ] Additional search engines (Yandex, Brave, etc.)
- [ ] Search result caching with TTL
- [ ] Pagination support
- [ ] Advanced filters (date, language, region)
- [ ] Async/concurrent search across multiple engines
- [ ] Search result deduplication
- [ ] API key authentication (optional)
- [ ] Metrics and monitoring dashboard
- [ ] Residential proxy rotation for Google bypass

---

**Happy Searching! 🔍**
