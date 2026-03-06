# Changelog

All notable changes to the Scrapling Search API will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.1.0] - 2026-03-06

### 🎉 Major Improvements

#### DuckDuckGo Engine - Bot Detection & Rate Limiting RESOLVED ✅
Complete rewrite of DuckDuckGo engine using **Scrapling library** to bypass bot detection and rate limiting.

**Changed:**
- Migrated from `httpx` to `scrapling.Fetcher` for HTTP requests
- Scrapling uses `curl_cffi` under the hood, providing realistic browser fingerprints
- Successfully bypasses HTTP 403 Forbidden and HTTP 202 rate limit responses

**Results:**
- ✅ DuckDuckGo now consistently returns quality search results
- ✅ Rate limiting issues completely resolved
- ✅ No more IP blocking problems

**Technical Details:**
```python
# Old (v2.0.0): httpx-based
async with httpx.AsyncClient() as client:
    response = await client.get(url, headers=headers)

# New (v2.1.0): Scrapling-based
from scrapling import Fetcher
fetcher = Fetcher()
page = fetcher.get(url)  # Bypasses bot detection
results = page.css('div.result')  # CSS selection
```

#### Google Engine - Playwright Integration 🔄
Implemented **Playwright browser automation** for Google search to handle JavaScript-heavy pages.

**Changed:**
- Migrated from `httpx` to `playwright` for browser automation
- Added headless Chromium browser with `networkidle` wait strategy
- Implemented wait for `div#search` selector before parsing

**Status:**
- ⚠️ Google's bot detection still blocks results (returns 0 results)
- ✅ Falls back gracefully to DuckDuckGo/Bing (no user-facing errors)
- ✅ Circuit breaker prevents wasted requests after 3 failures

**Technical Details:**
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, wait_until='networkidle', timeout=30000)
    page.wait_for_selector('div#search', timeout=10000)
    results = self._parse_results_playwright(page, limit)
```

### 🛡️ New: Circuit Breaker Pattern
Enhanced `EngineManager` with circuit breaker logic to optimize performance.

**Added:**
- Tracks consecutive failures per engine
- Disables engine after 3 consecutive failures
- Re-enables engine after 5-minute cooldown period
- Prevents wasting time on consistently failing engines

**Implementation:**
- `engine_failures`: Dict tracking consecutive failure counts
- `engine_disabled_until`: Dict tracking cooldown timestamps
- Automatic recovery when cooldown expires

### ⚙️ Configuration Updates

**Changed in `app/config.py`:**
- Version bumped to `2.1.0`
- `REQUEST_DELAY`: Increased from `1.0s` to `2.0s` (more conservative rate limiting)
- Added `SCRAPLING_TIMEOUT`: 30 seconds
- Added `SCRAPLING_AUTO_MATCH`: Enables automatic element matching

**New Dependencies:**
- `scrapling>=0.2.0` (installed v0.4.1)
- `playwright>=1.40.0` (optional, for Google engine)

### 📦 Dependencies

#### Added
- `scrapling>=0.2.0` - Anti-bot scraping library using curl_cffi
- `playwright>=1.40.0` - Browser automation (optional)

#### Updated
- `pydantic-settings==2.7.1` - Settings management (previously missing)

### 🔧 Technical Changes

**Modified Files:**
- `app/engines/duckduckgo.py` - Complete rewrite with Scrapling
- `app/engines/google.py` - Complete rewrite with Playwright
- `app/engines/manager.py` - Added circuit breaker pattern
- `app/config.py` - Version, delays, and Scrapling settings
- `requirements.txt` - Added scrapling and playwright

**Engine Fallback Order Changed:**
- **Old:** `[DuckDuckGoEngine, BingEngine, GoogleEngine]`
- **New:** `[GoogleEngine, DuckDuckGoEngine, BingEngine]` (quality-first approach)

Note: Since Google still gets blocked, effectively falls back to DuckDuckGo immediately.

### 📊 Testing & Validation

**Tested:**
- ✅ DuckDuckGo: Returns 5 results consistently
- ✅ Bing: Returns 5 results consistently  
- ⚠️ Google: Implemented but blocked (falls back gracefully)
- ✅ API endpoint `/search`: Fallback works correctly
- ✅ Response includes `engine_used` field

**Example API Response:**
```json
{
  "query": "python",
  "count": 3,
  "results": [
    {
      "title": "Welcome to Python.org",
      "snippet": "...",
      "url": "https://www.python.org/"
    }
  ],
  "sources": null,
  "engine_used": "duckduckgo",
  "error": null
}
```

### 📚 Documentation Updates

**Updated:**
- `TECHNICAL_DOCUMENTATION.md`:
  - Version to 2.1.0
  - Architecture diagram with Scrapling/Playwright
  - Known Issues section with resolution status
  - Technical stack with new dependencies
  
- `README.md`:
  - Features highlighting v2.1.0 improvements
  - Dependencies list with scrapling and playwright
  - Health check responses showing v2.1.0
  - Roadmap with completed v2.1.0 items

**Created:**
- `CHANGELOG.md` - This file

### 🎯 Production Readiness

**Status:** ✅ Production-Ready for Single-User Deployment (100-1000 req/day)

**What Works:**
- DuckDuckGo: Primary engine, fully functional
- Bing: Reliable backup, fully functional
- Automatic fallback: Seamless engine switching
- Circuit breaker: Optimizes performance by skipping failing engines

**Known Limitations:**
- Google: Still blocked by bot detection (falls back automatically)
- No caching layer (not needed for single-user deployment)
- No Redis integration (not needed at this scale)

### 🚀 Deployment Notes

**Requirements:**
```bash
pip install -r requirements.txt

# Optional: Install Playwright browsers (only if using Google engine)
python -m playwright install chromium
```

**Environment Variables:**
- No changes to existing environment variables
- All new settings have sensible defaults

**Docker:**
- Existing Dockerfile compatible
- May need to install Playwright browsers if using Google engine:
  ```dockerfile
  RUN python -m playwright install --with-deps chromium
  ```

---

## [2.0.0] - 2026-03-06

### Initial Release

**Features:**
- Multi-engine support (DuckDuckGo, Bing, Google)
- Automatic fallback between engines
- Source filtering by domain
- FastAPI-based REST API
- Interactive API documentation (/docs)
- Docker support
- Google Cloud Run ready

**Known Issues:**
- 🔴 Google: Blocked by bot detection
- 🔴 DuckDuckGo: Rate limiting (HTTP 403/202)
- 🟢 Bing: Working reliably

---

## Legend

- ✅ Resolved/Working
- ⚠️ Partially working/Known limitations
- 🔴 Broken/Not working
- 🟢 Working reliably
