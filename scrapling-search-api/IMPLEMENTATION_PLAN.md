# Scrapling Search API - Implementation Plan
**Version:** 2.0.0 → 2.1.0  
**Target:** Single-user production API (100-1000 req/day)  
**Date:** March 6, 2026  
**Goal:** Fix Google and DuckDuckGo engines using Scrapling library

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Phase 0: Prerequisites](#phase-0-prerequisites)
3. [Phase 1: Google Engine Migration](#phase-1-google-engine-migration)
4. [Phase 2: DuckDuckGo Engine Migration](#phase-2-duckduckgo-engine-migration)
5. [Phase 3: Engine Manager Enhancement](#phase-3-engine-manager-enhancement)
6. [Phase 4: Configuration Updates](#phase-4-configuration-updates)
7. [Phase 5: Testing & Validation](#phase-5-testing--validation)
8. [Phase 6: Documentation Updates](#phase-6-documentation-updates)
9. [Phase 7: Optional Enhancements](#phase-7-optional-enhancements)

---

## Overview

### Current Issues
- ❌ **Google Engine:** Returns 0 results (bot detection blocking CSS selectors)
- ❌ **DuckDuckGo Engine:** HTTP 403/202 (rate limited/IP blocked)
- ✅ **Bing Engine:** Working (keep as-is)

### Solution
- Use **Scrapling library** with anti-detection features
- Replace Google and DuckDuckGo engine implementations
- Keep existing architecture (no Redis/complex features needed)

### Success Criteria
- ✅ Google returns >0 results consistently
- ✅ DuckDuckGo returns >0 results without rate limits
- ✅ Fallback chain works: Google → DuckDuckGo → Bing
- ✅ Response time: <2 seconds average
- ✅ All existing API endpoints remain functional

---

## Phase 0: Prerequisites

### 0.1 Install Scrapling Library

**Action:** Add dependency and install

**File:** `requirements.txt`

**MODIFY:** Add new dependency
```diff
  fastapi==0.115.12
  uvicorn[standard]==0.32.1
  httpx==0.28.1
  lxml==5.3.0
  pydantic==2.10.6
  pydantic-settings==2.7.1
  python-dotenv==1.0.1
+ scrapling>=0.2.0
```

**Command to run:**
```bash
cd scrapling-search-api
pip install scrapling
```

**Validation:**
```python
python -c "from scrapling.fetchers import StealthyFetcher; print('Scrapling installed successfully')"
```

---

### 0.2 Test Scrapling with Google (Manual Test)

**Action:** Verify Scrapling can scrape Google successfully

**Create test file:** `test_scrapling_google.py` (temporary, delete after)

**Content:**
```python
"""
Temporary test file to verify Scrapling works with Google
Delete this file after Phase 5 validation
"""
from scrapling.fetchers import StealthyFetcher

def test_google_scraping():
    print("Testing Scrapling with Google search...")
    
    fetcher = StealthyFetcher()
    url = "https://www.google.com/search?q=python+programming&num=10"
    
    try:
        page = fetcher.get(url)
        print(f"Status: {page.status}")
        
        # Test various selectors
        selectors = [
            'div.g',
            'div[data-sokoban-container]',
            'div.Gx5Zad',
            'div:has(h3)',
        ]
        
        for selector in selectors:
            elements = page.css(selector)
            print(f"Selector '{selector}': Found {len(elements)} elements")
            
            if len(elements) > 0:
                print(f"✅ Working selector: {selector}")
                
                # Try to extract title from first result
                first = elements[0]
                title = first.css('h3::text').get()
                link = first.css('a::attr(href)').get()
                print(f"   Sample title: {title}")
                print(f"   Sample link: {link}")
                break
        else:
            print("❌ No selectors returned results")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_google_scraping()
```

**Command to run:**
```bash
python test_scrapling_google.py
```

**Expected output:**
```
Testing Scrapling with Google search...
Status: 200
Selector 'div.g': Found 10 elements
✅ Working selector: div.g
   Sample title: Welcome to Python.org
   Sample link: https://www.python.org/
```

**If test fails:** Scrapling may not work for your region/IP. Consider:
- Try different fetchers (`AsyncFetcher`, `PlaywrightFetcher`)
- Use proxies (Phase 7)
- Fallback to Playwright only

---

### 0.3 Test Scrapling with DuckDuckGo (Manual Test)

**Create test file:** `test_scrapling_duckduckgo.py` (temporary, delete after)

**Content:**
```python
"""
Temporary test file to verify Scrapling works with DuckDuckGo
Delete this file after Phase 5 validation
"""
from scrapling.fetchers import StealthyFetcher
import time

def test_duckduckgo_scraping():
    print("Testing Scrapling with DuckDuckGo search...")
    
    fetcher = StealthyFetcher()
    url = "https://html.duckduckgo.com/html/?q=python+programming"
    
    try:
        # Add delay to avoid rate limiting
        time.sleep(2)
        
        page = fetcher.get(url)
        print(f"Status: {page.status}")
        
        # Test selectors
        selectors = [
            'div.result',
            'div.results_links',
            'div.web-result',
        ]
        
        for selector in selectors:
            elements = page.css(selector)
            print(f"Selector '{selector}': Found {len(elements)} elements")
            
            if len(elements) > 0:
                print(f"✅ Working selector: {selector}")
                
                # Try to extract title from first result
                first = elements[0]
                title = first.css('a.result__a::text').get()
                link = first.css('a.result__a::attr(href)').get()
                print(f"   Sample title: {title}")
                print(f"   Sample link: {link}")
                break
        else:
            print("❌ No selectors returned results")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_duckduckgo_scraping()
```

**Command to run:**
```bash
python test_scrapling_duckduckgo.py
```

**Expected output:**
```
Testing Scrapling with DuckDuckGo search...
Status: 200
Selector 'div.result': Found 10 elements
✅ Working selector: div.result
   Sample title: Welcome to Python.org
   Sample link: https://www.python.org/
```

---

## Phase 1: Google Engine Migration

### 1.1 Backup Current Google Engine

**Action:** Create backup before modifying

**Command:**
```bash
cd scrapling-search-api/app/engines
cp google.py google.old.py
```

**Purpose:** Rollback if Scrapling implementation fails

---

### 1.2 Rewrite Google Engine

**File:** `app/engines/google.py`

**REPLACE ENTIRE FILE with:**

```python
"""Google search engine implementation using Scrapling.

This module provides Google search functionality with anti-bot detection
using the Scrapling library's StealthyFetcher.
"""

import logging
from typing import List, Optional
import urllib.parse
from scrapling.fetchers import StealthyFetcher

from app.engines.base import BaseEngine
from app.models.schemas import SearchResult
from app.config import Settings

logger = logging.getLogger(__name__)


class GoogleEngine(BaseEngine):
    """Google search engine using Scrapling for anti-detection."""
    
    def __init__(self, settings: Settings):
        """Initialize Google engine with Scrapling fetcher.
        
        Args:
            settings: Application settings
        """
        super().__init__(settings)
        self.fetcher = StealthyFetcher()
        self.base_url = "https://www.google.com/search"
    
    @property
    def name(self) -> str:
        """Return engine name."""
        return "google"
    
    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Perform Google search using Scrapling.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
        """
        logger.info(f"[{self.name}] Starting search for: {query}")
        
        for attempt in range(1, self.settings.MAX_RETRIES + 1):
            try:
                logger.info(f"[{self.name}] Attempt {attempt}/{self.settings.MAX_RETRIES}")
                
                # Build search URL
                params = {
                    'q': query,
                    'num': min(limit, 50),  # Google max per page
                    'hl': 'en',
                }
                url = f"{self.base_url}?{urllib.parse.urlencode(params)}"
                
                logger.info(f"[{self.name}] Fetching: {url}")
                
                # Fetch page using Scrapling
                page = self.fetcher.get(url)
                
                logger.info(f"[{self.name}] Response status: {page.status}")
                
                if page.status != 200:
                    logger.error(f"[{self.name}] Non-200 status: {page.status}")
                    self._handle_delay(attempt)
                    continue
                
                # Parse results
                results = self._parse_results(page, limit)
                
                if results:
                    logger.info(f"[{self.name}] Successfully extracted {len(results)} results")
                    return results
                else:
                    logger.warning(f"[{self.name}] No results found (attempt {attempt})")
                    self._handle_delay(attempt)
                    
            except Exception as e:
                logger.error(f"[{self.name}] Error on attempt {attempt}: {e}")
                self._handle_delay(attempt)
        
        logger.error(f"[{self.name}] All retry attempts failed")
        return []
    
    def _parse_results(self, page, limit: int) -> List[SearchResult]:
        """Parse Google search results from page.
        
        Args:
            page: Scrapling page object
            limit: Maximum results to return
            
        Returns:
            List of SearchResult objects
        """
        results = []
        
        # Try multiple selectors (Google changes DOM frequently)
        selectors = [
            'div.g',                              # Standard desktop results
            'div[data-sokoban-container]',        # Alternative container
            'div.Gx5Zad',                         # Mobile results
            'div:has(h3)',                        # Fallback: any div with h3
        ]
        
        result_elements = []
        working_selector = None
        
        for selector in selectors:
            elements = page.css(selector)
            logger.info(f"[{self.name}] Selector '{selector}': Found {len(elements)} elements")
            
            if len(elements) > 0:
                result_elements = elements
                working_selector = selector
                logger.info(f"[{self.name}] Using working selector: {selector}")
                break
        
        if not result_elements:
            logger.error(f"[{self.name}] No result elements found with any selector")
            return []
        
        # Extract data from each result
        for idx, element in enumerate(result_elements[:limit]):
            try:
                # Extract title (multiple possible locations)
                title = None
                title_selectors = ['h3::text', 'h3 *::text', '[role="heading"]::text']
                for title_sel in title_selectors:
                    title = element.css(title_sel).get()
                    if title:
                        break
                
                # Extract URL
                url = None
                link_selectors = ['a::attr(href)', 'a[href]::attr(href)']
                for link_sel in link_selectors:
                    url = element.css(link_sel).get()
                    if url and url.startswith('http'):
                        break
                
                # Extract snippet/description
                snippet = None
                snippet_selectors = [
                    'div.VwiC3b::text',           # Standard snippet
                    'div[data-content-feature="1"]::text',
                    'span.aCOpRe::text',
                    'div.IsZvec::text',
                    'div *::text',                # Fallback: any text in div
                ]
                for snippet_sel in snippet_selectors:
                    snippet = element.css(snippet_sel).get()
                    if snippet and len(snippet.strip()) > 20:
                        break
                
                # Validate result
                if not title or not url:
                    logger.debug(f"[{self.name}] Skipping result {idx}: missing title or URL")
                    continue
                
                # Clean URL (remove Google tracking)
                if '/url?q=' in url:
                    url = urllib.parse.unquote(url.split('/url?q=')[1].split('&')[0])
                
                result = SearchResult(
                    title=title.strip(),
                    url=url.strip(),
                    snippet=snippet.strip() if snippet else ""
                )
                
                results.append(result)
                logger.debug(f"[{self.name}] Extracted result {len(results)}: {title[:50]}...")
                
            except Exception as e:
                logger.error(f"[{self.name}] Error parsing result {idx}: {e}")
                continue
        
        return results
```

**Changes made:**
- ✅ Replaced `httpx.AsyncClient` with `scrapling.fetchers.StealthyFetcher`
- ✅ Removed manual headers (Scrapling handles this)
- ✅ Updated CSS selectors to work with Scrapling's API
- ✅ Kept retry logic and error handling
- ✅ Maintained same interface (BaseEngine)
- ✅ Enhanced logging for debugging

---

## Phase 2: DuckDuckGo Engine Migration

### 2.1 Backup Current DuckDuckGo Engine

**Action:** Create backup before modifying

**Command:**
```bash
cd scrapling-search-api/app/engines
cp duckduckgo.py duckduckgo.old.py
```

---

### 2.2 Rewrite DuckDuckGo Engine

**File:** `app/engines/duckduckgo.py`

**REPLACE ENTIRE FILE with:**

```python
"""DuckDuckGo search engine implementation using Scrapling.

This module provides DuckDuckGo search functionality with anti-rate-limiting
using the Scrapling library.
"""

import logging
from typing import List
import urllib.parse
from scrapling.fetchers import StealthyFetcher
import time

from app.engines.base import BaseEngine
from app.models.schemas import SearchResult
from app.config import Settings

logger = logging.getLogger(__name__)


class DuckDuckGoEngine(BaseEngine):
    """DuckDuckGo search engine using Scrapling."""
    
    def __init__(self, settings: Settings):
        """Initialize DuckDuckGo engine with Scrapling fetcher.
        
        Args:
            settings: Application settings
        """
        super().__init__(settings)
        self.fetcher = StealthyFetcher()
        self.base_url = "https://html.duckduckgo.com/html/"
    
    @property
    def name(self) -> str:
        """Return engine name."""
        return "duckduckgo"
    
    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Perform DuckDuckGo search using Scrapling.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
        """
        logger.info(f"[{self.name}] Starting search for: {query}")
        
        for attempt in range(1, self.settings.MAX_RETRIES + 1):
            try:
                logger.info(f"[{self.name}] Attempt {attempt}/{self.settings.MAX_RETRIES}")
                
                # Add delay before request (DDG is sensitive to rapid requests)
                if attempt > 1:
                    delay = self.settings.REQUEST_DELAY * attempt
                    logger.info(f"[{self.name}] Waiting {delay}s before retry...")
                    time.sleep(delay)
                
                # Build search URL
                params = {'q': query}
                url = f"{self.base_url}?{urllib.parse.urlencode(params)}"
                
                logger.info(f"[{self.name}] Fetching: {url}")
                
                # Fetch page using Scrapling
                page = self.fetcher.get(url)
                
                logger.info(f"[{self.name}] Response status: {page.status}")
                
                # Check for rate limiting
                if page.status == 202:
                    logger.warning(f"[{self.name}] Rate limited (HTTP 202)")
                    time.sleep(5)
                    continue
                
                if page.status == 403:
                    logger.warning(f"[{self.name}] Access forbidden (HTTP 403)")
                    time.sleep(5)
                    continue
                
                if page.status != 200:
                    logger.error(f"[{self.name}] Non-200 status: {page.status}")
                    self._handle_delay(attempt)
                    continue
                
                # Parse results
                results = self._parse_results(page, limit)
                
                if results:
                    logger.info(f"[{self.name}] Successfully extracted {len(results)} results")
                    return results
                else:
                    logger.warning(f"[{self.name}] No results found (attempt {attempt})")
                    self._handle_delay(attempt)
                    
            except Exception as e:
                logger.error(f"[{self.name}] Error on attempt {attempt}: {e}")
                self._handle_delay(attempt)
        
        logger.error(f"[{self.name}] All retry attempts failed")
        return []
    
    def _parse_results(self, page, limit: int) -> List[SearchResult]:
        """Parse DuckDuckGo search results from page.
        
        Args:
            page: Scrapling page object
            limit: Maximum results to return
            
        Returns:
            List of SearchResult objects
        """
        results = []
        
        # Try multiple selectors
        selectors = [
            'div.result',
            'div.results_links',
            'div.web-result',
            'div[class*="result"]',
        ]
        
        result_elements = []
        working_selector = None
        
        for selector in selectors:
            elements = page.css(selector)
            logger.info(f"[{self.name}] Selector '{selector}': Found {len(elements)} elements")
            
            if len(elements) > 0:
                result_elements = elements
                working_selector = selector
                logger.info(f"[{self.name}] Using working selector: {selector}")
                break
        
        if not result_elements:
            logger.error(f"[{self.name}] No result elements found with any selector")
            return []
        
        # Extract data from each result
        for idx, element in enumerate(result_elements[:limit]):
            try:
                # Extract title
                title = None
                title_selectors = [
                    'a.result__a::text',
                    'h2.result__title::text',
                    'a.result-link::text',
                    'a::text',
                ]
                for title_sel in title_selectors:
                    title = element.css(title_sel).get()
                    if title:
                        break
                
                # Extract URL
                url = None
                link_selectors = [
                    'a.result__a::attr(href)',
                    'a.result-link::attr(href)',
                    'a::attr(href)',
                ]
                for link_sel in link_selectors:
                    url = element.css(link_sel).get()
                    if url:
                        break
                
                # Extract snippet
                snippet = None
                snippet_selectors = [
                    'a.result__snippet::text',
                    'div.result__snippet::text',
                    'div.snippet::text',
                    'div *::text',
                ]
                for snippet_sel in snippet_selectors:
                    snippet = element.css(snippet_sel).get()
                    if snippet and len(snippet.strip()) > 10:
                        break
                
                # Validate result
                if not title or not url:
                    logger.debug(f"[{self.name}] Skipping result {idx}: missing title or URL")
                    continue
                
                # Clean URL (DuckDuckGo uses redirect URLs)
                if url.startswith('//duckduckgo.com/l/?'):
                    # Extract actual URL from redirect parameter
                    try:
                        parsed = urllib.parse.urlparse(url)
                        params = urllib.parse.parse_qs(parsed.query)
                        if 'uddg' in params:
                            url = urllib.parse.unquote(params['uddg'][0])
                    except:
                        pass
                
                # Ensure URL has protocol
                if url.startswith('//'):
                    url = 'https:' + url
                elif not url.startswith('http'):
                    url = 'https://' + url
                
                result = SearchResult(
                    title=title.strip(),
                    url=url.strip(),
                    snippet=snippet.strip() if snippet else ""
                )
                
                results.append(result)
                logger.debug(f"[{self.name}] Extracted result {len(results)}: {title[:50]}...")
                
            except Exception as e:
                logger.error(f"[{self.name}] Error parsing result {idx}: {e}")
                continue
        
        return results
```

**Changes made:**
- ✅ Replaced `httpx.AsyncClient` with `scrapling.fetchers.StealthyFetcher`
- ✅ Added extra delays to avoid rate limiting
- ✅ Enhanced handling of HTTP 202/403 responses
- ✅ Updated URL extraction logic
- ✅ Maintained retry logic
- ✅ Better error handling

---

## Phase 3: Engine Manager Enhancement

### 3.1 Update Engine Manager Fallback Logic

**File:** `app/engines/manager.py`

**MODIFY:** Enhance fallback mechanism and add circuit breaker pattern

**Find this section (around line 15-40):**
```python
class EngineManager:
    """Manages multiple search engines with fallback support."""
    
    def __init__(self, settings: Settings):
        """Initialize engine manager with all available engines."""
        self.settings = settings
        self.engines = [
            DuckDuckGoEngine(settings),
            BingEngine(settings),
            GoogleEngine(settings),
        ]
```

**REPLACE with:**
```python
class EngineManager:
    """Manages multiple search engines with intelligent fallback support."""
    
    def __init__(self, settings: Settings):
        """Initialize engine manager with all available engines."""
        self.settings = settings
        
        # Initialize engines
        self.engines = [
            GoogleEngine(settings),        # Try Google first (best quality)
            DuckDuckGoEngine(settings),    # Fallback to DuckDuckGo
            BingEngine(settings),          # Final fallback to Bing
        ]
        
        # Track engine health (simple circuit breaker)
        self.engine_failures = {engine.name: 0 for engine in self.engines}
        self.engine_disabled_until = {engine.name: 0 for engine in self.engines}
```

**Find the search method (around line 45-80):**
```python
    def search(
        self,
        query: str,
        limit: int = 10,
        preferred_engine: Optional[str] = None,
        strict_mode: bool = False
    ) -> tuple[List[SearchResult], Optional[str]]:
```

**REPLACE the entire method with:**
```python
    def search(
        self,
        query: str,
        limit: int = 10,
        preferred_engine: Optional[str] = None,
        strict_mode: bool = False
    ) -> tuple[List[SearchResult], Optional[str]]:
        """Search using engines with intelligent fallback.
        
        Args:
            query: Search query
            limit: Maximum results
            preferred_engine: Preferred engine name (e.g., "google")
            strict_mode: If True, only use preferred engine (no fallback)
            
        Returns:
            Tuple of (results list, engine name used)
        """
        logger.info(f"[EngineManager] Starting search: query='{query}', preferred='{preferred_engine}', strict={strict_mode}")
        
        # Determine engine order
        if preferred_engine:
            engines_to_try = self._get_engine_order(preferred_engine)
        else:
            engines_to_try = self.engines.copy()
        
        # In strict mode, only try the preferred engine
        if strict_mode and preferred_engine:
            engines_to_try = [e for e in engines_to_try if e.name == preferred_engine]
            if not engines_to_try:
                logger.error(f"[EngineManager] Preferred engine '{preferred_engine}' not found")
                return [], None
        
        # Try engines in order until one succeeds
        for engine in engines_to_try:
            # Check if engine is temporarily disabled (circuit breaker)
            if self._is_engine_disabled(engine.name):
                logger.warning(f"[EngineManager] Engine '{engine.name}' is temporarily disabled")
                continue
            
            logger.info(f"[EngineManager] Trying engine: {engine.name}")
            
            try:
                results = engine.search(query, limit)
                
                if results and len(results) > 0:
                    logger.info(f"[EngineManager] Success with {engine.name}: {len(results)} results")
                    
                    # Reset failure count on success
                    self.engine_failures[engine.name] = 0
                    
                    return results, engine.name
                else:
                    logger.warning(f"[EngineManager] Engine {engine.name} returned 0 results")
                    self._record_failure(engine.name)
                    
            except Exception as e:
                logger.error(f"[EngineManager] Engine {engine.name} error: {e}")
                self._record_failure(engine.name)
                continue
        
        logger.error(f"[EngineManager] All engines failed for query: {query}")
        return [], None
    
    def _get_engine_order(self, preferred_engine: str) -> List:
        """Get engines in order with preferred engine first.
        
        Args:
            preferred_engine: Name of preferred engine
            
        Returns:
            List of engines with preferred one first
        """
        preferred = None
        others = []
        
        for engine in self.engines:
            if engine.name == preferred_engine:
                preferred = engine
            else:
                others.append(engine)
        
        if preferred:
            return [preferred] + others
        else:
            return self.engines.copy()
    
    def _is_engine_disabled(self, engine_name: str) -> bool:
        """Check if engine is temporarily disabled by circuit breaker.
        
        Args:
            engine_name: Name of engine to check
            
        Returns:
            True if engine is disabled, False otherwise
        """
        import time
        disabled_until = self.engine_disabled_until.get(engine_name, 0)
        
        if disabled_until > time.time():
            return True
        
        # Re-enable if cooldown period passed
        if disabled_until > 0:
            logger.info(f"[EngineManager] Re-enabling engine: {engine_name}")
            self.engine_disabled_until[engine_name] = 0
            self.engine_failures[engine_name] = 0
        
        return False
    
    def _record_failure(self, engine_name: str):
        """Record engine failure and disable if threshold reached.
        
        Args:
            engine_name: Name of engine that failed
        """
        import time
        
        self.engine_failures[engine_name] = self.engine_failures.get(engine_name, 0) + 1
        failures = self.engine_failures[engine_name]
        
        logger.warning(f"[EngineManager] Engine {engine_name} failure count: {failures}")
        
        # Disable engine after 3 consecutive failures (circuit breaker)
        if failures >= 3:
            cooldown_seconds = 300  # 5 minutes
            self.engine_disabled_until[engine_name] = time.time() + cooldown_seconds
            logger.warning(
                f"[EngineManager] Disabling engine {engine_name} for {cooldown_seconds}s "
                f"due to {failures} consecutive failures"
            )
```

**Changes made:**
- ✅ Changed engine order to Google → DuckDuckGo → Bing (quality-based)
- ✅ Added circuit breaker pattern (disables failing engines temporarily)
- ✅ Enhanced logging for better debugging
- ✅ Cleaner engine selection logic
- ✅ Better error handling

---

## Phase 4: Configuration Updates

### 4.1 Update Settings

**File:** `app/config.py`

**FIND (around end of Settings class):**
```python
class Settings(BaseSettings):
    # ... existing settings ...
    MAX_RETRIES: int = 3
    REQUEST_DELAY: float = 1.0
```

**ADD after existing settings:**
```python
    # Scrapling-specific settings
    SCRAPLING_TIMEOUT: int = 30
    SCRAPLING_AUTO_MATCH: bool = True  # Auto-match selectors when page changes
```

**MODIFY (if exists) or ADD:**
```python
    # Engine settings
    MAX_RETRIES: int = 3
    REQUEST_DELAY: float = 2.0  # Increased from 1.0 to 2.0 for better rate limit avoidance
    HTTP_TIMEOUT: int = 30
```

**Full updated config.py should look like:**
```python
"""Application configuration settings."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Metadata
    API_TITLE: str = "Scrapling Search API"
    API_VERSION: str = "2.1.0"  # Updated from 2.0.0
    API_DESCRIPTION: str = "Free web search API with multi-engine support and Scrapling integration"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    LOG_LEVEL: str = "INFO"
    
    # Search engine settings
    MAX_RETRIES: int = 3
    REQUEST_DELAY: float = 2.0  # Increased for rate limit avoidance
    HTTP_TIMEOUT: int = 30
    
    # Scrapling settings
    SCRAPLING_TIMEOUT: int = 30
    SCRAPLING_AUTO_MATCH: bool = True
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = True


def get_settings() -> Settings:
    """Get application settings singleton.
    
    Returns:
        Settings instance
    """
    return Settings()
```

---

### 4.2 Update Environment Variables

**File:** `.env` (create if doesn't exist)

**ADD/UPDATE:**
```bash
# API Configuration
API_TITLE=Scrapling Search API
API_VERSION=2.1.0
LOG_LEVEL=INFO

# Engine Configuration
MAX_RETRIES=3
REQUEST_DELAY=2.0
HTTP_TIMEOUT=30

# Scrapling Configuration
SCRAPLING_TIMEOUT=30
SCRAPLING_AUTO_MATCH=true
```

---

## Phase 5: Testing & Validation

### 5.1 Unit Tests for Individual Engines

**CREATE:** `test_engines.py` (temporary test file)

```python
"""
Test individual search engines
Run: python test_engines.py
Delete after validation
"""

import sys
sys.path.insert(0, '.')

from app.config import get_settings
from app.engines.google import GoogleEngine
from app.engines.duckduckgo import DuckDuckGoEngine
from app.engines.bing import BingEngine

def test_engine(engine, query="python programming"):
    """Test a single engine."""
    print(f"\n{'='*60}")
    print(f"Testing {engine.name.upper()} Engine")
    print(f"{'='*60}")
    
    try:
        results = engine.search(query, limit=5)
        
        if results:
            print(f"✅ SUCCESS: Found {len(results)} results\n")
            
            for i, result in enumerate(results, 1):
                print(f"Result {i}:")
                print(f"  Title: {result.title[:80]}")
                print(f"  URL: {result.url}")
                print(f"  Snippet: {result.snippet[:100]}...")
                print()
        else:
            print(f"❌ FAILED: No results found")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

def main():
    settings = get_settings()
    
    # Test Google
    google = GoogleEngine(settings)
    test_engine(google)
    
    # Test DuckDuckGo
    duckduckgo = DuckDuckGoEngine(settings)
    test_engine(duckduckgo)
    
    # Test Bing
    bing = BingEngine(settings)
    test_engine(bing)

if __name__ == "__main__":
    main()
```

**Command:**
```bash
cd scrapling-search-api
python test_engines.py
```

**Expected output:**
```
============================================================
Testing GOOGLE Engine
============================================================
✅ SUCCESS: Found 5 results

Result 1:
  Title: Welcome to Python.org
  URL: https://www.python.org/
  Snippet: The official home of the Python Programming Language...

[... more results ...]

============================================================
Testing DUCKDUCKGO Engine
============================================================
✅ SUCCESS: Found 5 results
[...]

============================================================
Testing BING Engine
============================================================
✅ SUCCESS: Found 5 results
[...]
```

---

### 5.2 Integration Test - Full API

**Command:**
```bash
# Start server
cd scrapling-search-api
uvicorn main:app --reload --port 8080
```

**In another terminal, test all engines:**

```bash
# Test Google engine
curl "http://localhost:8080/search?q=python&limit=5&engine=google"

# Test DuckDuckGo engine
curl "http://localhost:8080/search?q=python&limit=5&engine=duckduckgo"

# Test Bing engine
curl "http://localhost:8080/search?q=python&limit=5&engine=bing"

# Test automatic fallback (no engine specified)
curl "http://localhost:8080/search?q=python&limit=5"

# Test with source filtering
curl "http://localhost:8080/search?q=python&sources=python.org,github.com"
```

**Expected responses:**
- All engines return results (count > 0)
- Response time < 3 seconds
- No errors in logs
- Fallback works if primary engine fails

---

### 5.3 Validation Checklist

**Run through this checklist:**

- [ ] Google engine returns >0 results
- [ ] DuckDuckGo engine returns >0 results  
- [ ] Bing engine still works (unchanged)
- [ ] Fallback order works: Google → DDG → Bing
- [ ] API `/search` endpoint works
- [ ] API `/health` endpoint works
- [ ] Source filtering still works
- [ ] Strict mode works (`strict=true`)
- [ ] No import errors on server start
- [ ] Logs show clear engine selection flow
- [ ] Response times acceptable (<3s)

**If any test fails:**
1. Check logs for errors
2. Review Phase 0 manual tests
3. Verify Scrapling is installed correctly
4. Check CSS selectors are working
5. Consider adding delays or retry attempts

---

### 5.4 Cleanup Test Files

**After validation passes, delete temporary test files:**

```bash
cd scrapling-search-api
rm test_scrapling_google.py
rm test_scrapling_duckduckgo.py
rm test_engines.py
```

---

## Phase 6: Documentation Updates

### 6.1 Update Technical Documentation

**File:** `TECHNICAL_DOCUMENTATION.md`

**FIND section:** `## Known Issues` → `### 🔴 Critical Issues`

**UPDATE both Google and DuckDuckGo issue status:**

**Find:**
```markdown
#### 1. **Google Search Engine - Bot Detection Blocking**
**Status:** Blocked
```

**REPLACE with:**
```markdown
#### 1. **Google Search Engine - Bot Detection Blocking**
**Status:** ✅ RESOLVED (v2.1.0)
**Solution:** Migrated to Scrapling library with StealthyFetcher
**Date Fixed:** March 6, 2026
```

**Find:**
```markdown
#### 2. **DuckDuckGo - Rate Limiting / IP Blocking**
**Status:** Rate-limited
```

**REPLACE with:**
```markdown
#### 2. **DuckDuckGo - Rate Limiting / IP Blocking**
**Status:** ✅ RESOLVED (v2.1.0)
**Solution:** Migrated to Scrapling library with enhanced delay logic
**Date Fixed:** March 6, 2026
```

**FIND section:** `## Technical Stack`

**UPDATE Core Dependencies section:**
```markdown
### Core Dependencies
```

**ADD Scrapling:**
```markdown
### Core Dependencies
```python
fastapi==0.115.12           # Web framework
uvicorn[standard]==0.32.1   # ASGI server
httpx==0.28.1               # HTTP client (Bing engine only)
scrapling>=0.2.0            # Advanced web scraping with anti-detection ✨ NEW
lxml==5.3.0                 # HTML parsing
pydantic==2.10.6           # Data validation
pydantic-settings==2.7.1   # Settings management
python-dotenv==1.0.1       # Environment variables
```
```

**FIND section:** `## Architecture` → Engine Layer

**UPDATE Engine Layer description:**
```markdown
#### 3. **Engine Layer** (Data Access)
- **Purpose:** Abstract search engine implementations
- **Design Pattern:** Strategy Pattern
- **Components:**
  - `engines/base.py` - BaseEngine abstract class
  - `engines/manager.py` - EngineManager with circuit breaker
  - `engines/google.py` - Google (Scrapling-based) ✅ Working
  - `engines/duckduckgo.py` - DuckDuckGo (Scrapling-based) ✅ Working
  - `engines/bing.py` - Bing (httpx-based) ✅ Working
```

---

### 6.2 Update README

**File:** `README.md`

**FIND version/status section (usually near top):**

**UPDATE:**
```markdown
# Scrapling Search API

**Version:** 2.1.0  
**Status:** ✅ Production Ready  
**Updated:** March 6, 2026

Free web search API with multi-engine support powered by Scrapling.

## ✨ What's New in v2.1.0
- ✅ **Fixed Google Engine:** Now uses Scrapling with anti-bot detection
- ✅ **Fixed DuckDuckGo Engine:** Enhanced rate limit handling with Scrapling
- ✅ **All engines working:** Google, DuckDuckGo, and Bing all operational
- ✅ **Circuit breaker pattern:** Automatically disables failing engines temporarily
- ✅ **Improved fallback:** Intelligent engine selection (Google → DDG → Bing)
```

**FIND Features section:**

**UPDATE:**
```markdown
## Features

✅ **Multi-Engine Support**
- Google Search (Scrapling-powered, anti-detection)
- DuckDuckGo Search (Scrapling-powered, rate-limit resistant)
- Bing Search (reliable fallback)

✅ **Intelligent Fallback**
- Automatic failover: Google → DuckDuckGo → Bing
- Circuit breaker: disables failing engines temporarily
- Configurable engine preference

✅ **Advanced Scraping**
- Scrapling library integration
- Anti-bot detection bypass
- Automatic selector matching

✅ **Source Filtering**
- Filter by domain (e.g., `python.org`)
- Subdomain matching

✅ **Developer Friendly**
- OpenAPI/Swagger docs at `/docs`
- Health check endpoint
- Comprehensive logging
```

---

### 6.3 Update Changelog

**CREATE/UPDATE:** `CHANGELOG.md`

```markdown
# Changelog

All notable changes to Scrapling Search API will be documented in this file.

## [2.1.0] - 2026-03-06

### 🎉 Added
- Scrapling library integration for advanced web scraping
- Circuit breaker pattern in EngineManager
- Enhanced health check showing engine status
- Automatic selector matching (Scrapling feature)
- Better rate limit handling for DuckDuckGo

### 🔧 Fixed
- **CRITICAL:** Google engine now returns results (was blocked by bot detection)
- **CRITICAL:** DuckDuckGo engine now works (was rate-limited)
- Fallback chain now prioritizes quality (Google first, then DDG, then Bing)

### 🔄 Changed
- Google engine: Replaced httpx with Scrapling StealthyFetcher
- DuckDuckGo engine: Replaced httpx with Scrapling StealthyFetcher
- REQUEST_DELAY increased from 1.0s to 2.0s (better rate limit avoidance)
- Engine order: Google → DuckDuckGo → Bing (was DDG → Bing → Google)
- API version bumped to 2.1.0

### 📦 Dependencies
- Added: `scrapling>=0.2.0`

### 🗑️ Removed
- None (backward compatible)

---

## [2.0.0] - 2026-03-05

### Initial Release
- FastAPI-based search API
- Multi-engine support (Google, DuckDuckGo, Bing)
- Source filtering
- OpenAPI documentation

### Known Issues (Fixed in 2.1.0)
- Google engine blocked by bot detection
- DuckDuckGo rate limited
```

---

## Phase 7: Optional Enhancements

### 7.1 Add Simple In-Memory Cache (Optional)

**Only implement if you want to cache repeated searches**

**CREATE:** `app/services/cache_service.py`

```python
"""Simple in-memory cache for search results.

This is a lightweight caching solution that doesn't require Redis.
Suitable for single-instance deployments.
"""

import threading
import hashlib
from typing import Optional, List
from cachetools import TTLCache
from app.models.schemas import SearchResult
import logging

logger = logging.getLogger(__name__)


class SimpleCache:
    """Thread-safe in-memory cache for search results."""
    
    def __init__(self, maxsize: int = 200, ttl: int = 300):
        """Initialize cache.
        
        Args:
            maxsize: Maximum number of cached queries
            ttl: Time-to-live in seconds (default: 5 minutes)
        """
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0
    
    def _make_key(self, query: str, limit: int, sources: Optional[str], engine: Optional[str]) -> str:
        """Generate cache key from search parameters.
        
        Args:
            query: Search query
            limit: Result limit
            sources: Source filter
            engine: Engine name
            
        Returns:
            Cache key string
        """
        key_parts = [
            query.lower().strip(),
            str(limit),
            sources or "",
            engine or ""
        ]
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, query: str, limit: int, sources: Optional[str], engine: Optional[str]) -> Optional[tuple]:
        """Get cached results.
        
        Args:
            query: Search query
            limit: Result limit
            sources: Source filter
            engine: Engine name
            
        Returns:
            Tuple of (results, engine_used) or None if not cached
        """
        key = self._make_key(query, limit, sources, engine)
        
        with self.lock:
            cached = self.cache.get(key)
            
            if cached:
                self.hits += 1
                logger.info(f"[Cache] HIT for query: {query}")
                return cached
            else:
                self.misses += 1
                logger.info(f"[Cache] MISS for query: {query}")
                return None
    
    def set(self, query: str, limit: int, sources: Optional[str], engine: Optional[str], 
            results: List[SearchResult], engine_used: str):
        """Store results in cache.
        
        Args:
            query: Search query
            limit: Result limit
            sources: Source filter
            engine: Engine name
            results: Search results to cache
            engine_used: Name of engine that returned results
        """
        key = self._make_key(query, limit, sources, engine)
        
        with self.lock:
            self.cache[key] = (results, engine_used)
            logger.info(f"[Cache] SET for query: {query} ({len(results)} results)")
    
    def get_stats(self) -> dict:
        """Get cache statistics.
        
        Returns:
            Dict with cache stats
        """
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        with self.lock:
            return {
                "size": len(self.cache),
                "maxsize": self.cache.maxsize,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": f"{hit_rate:.1f}%"
            }
    
    def clear(self):
        """Clear all cached data."""
        with self.lock:
            self.cache.clear()
            logger.info("[Cache] Cleared all cached data")


# Singleton instance
_cache_instance = None


def get_cache() -> SimpleCache:
    """Get cache singleton instance.
    
    Returns:
        SimpleCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SimpleCache(maxsize=200, ttl=300)
    return _cache_instance
```

**MODIFY:** `app/services/search_service.py`

**ADD import at top:**
```python
from app.services.cache_service import get_cache
```

**MODIFY search method to use cache:**

**Find:**
```python
def search(
    self,
    query: str,
    limit: int = 10,
    sources: Optional[str] = None,
    preferred_engine: Optional[str] = None,
    strict_mode: bool = False
) -> SearchResponse:
```

**REPLACE method body with:**
```python
def search(
    self,
    query: str,
    limit: int = 10,
    sources: Optional[str] = None,
    preferred_engine: Optional[str] = None,
    strict_mode: bool = False
) -> SearchResponse:
    """Perform search with caching support."""
    
    cache = get_cache()
    
    # Try to get from cache
    cached = cache.get(query, limit, sources, preferred_engine)
    if cached:
        results, engine_used = cached
        logger.info(f"[SearchService] Returning cached results ({len(results)} items)")
        
        return SearchResponse(
            query=query,
            count=len(results),
            results=results,
            sources=list(sources.split(",")) if sources else None,
            engine_used=engine_used,
            error=None
        )
    
    # Cache miss - perform search
    results, engine_used = self.engine_manager.search(
        query=query,
        limit=limit,
        preferred_engine=preferred_engine,
        strict_mode=strict_mode
    )
    
    if not results:
        return SearchResponse(
            query=query,
            count=0,
            results=[],
            sources=None,
            engine_used=engine_used,
            error="No results found from any engine"
        )
    
    # Apply source filtering if specified
    if sources:
        results = self._apply_source_filter(results, sources)
    
    # Store in cache
    cache.set(query, limit, sources, preferred_engine, results, engine_used)
    
    return SearchResponse(
        query=query,
        count=len(results),
        results=results,
        sources=list(sources.split(",")) if sources else None,
        engine_used=engine_used,
        error=None
    )
```

**ADD cache stats endpoint:**

**MODIFY:** `app/routes/health.py`

**ADD import:**
```python
from app.services.cache_service import get_cache
```

**ADD new endpoint:**
```python
@router.get("/health/cache")
async def cache_stats():
    """Get cache statistics."""
    cache = get_cache()
    return cache.get_stats()
```

**UPDATE requirements.txt:**
```diff
+ cachetools>=5.3.0
```

---

### 7.2 Add Playwright Fallback (Optional)

**Only if Scrapling fails for some engines**

**CREATE:** `app/engines/playwright_engine.py`

```python
"""Playwright-based search engine fallback.

Use when Scrapling fails. Slower but more reliable for heavily protected sites.
"""

import logging
from typing import List
from playwright.sync_api import sync_playwright
import urllib.parse

from app.engines.base import BaseEngine
from app.models.schemas import SearchResult
from app.config import Settings

logger = logging.getLogger(__name__)


class PlaywrightGoogleEngine(BaseEngine):
    """Google search using Playwright (heavy fallback)."""
    
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.base_url = "https://www.google.com/search"
    
    @property
    def name(self) -> str:
        return "google-playwright"
    
    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Search using Playwright browser automation."""
        logger.info(f"[{self.name}] Starting browser-based search")
        
        results = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                url = f"{self.base_url}?q={urllib.parse.quote(query)}&num={limit}"
                page.goto(url, wait_until="networkidle")
                
                # Wait for results
                page.wait_for_selector('div.g', timeout=10000)
                
                # Extract results
                elements = page.query_selector_all('div.g')
                
                for element in elements[:limit]:
                    try:
                        title_el = element.query_selector('h3')
                        link_el = element.query_selector('a')
                        snippet_el = element.query_selector('div.VwiC3b')
                        
                        if title_el and link_el:
                            title = title_el.inner_text()
                            url = link_el.get_attribute('href')
                            snippet = snippet_el.inner_text() if snippet_el else ""
                            
                            results.append(SearchResult(
                                title=title,
                                url=url,
                                snippet=snippet
                            ))
                    except Exception as e:
                        logger.error(f"Error extracting result: {e}")
                        continue
                
                logger.info(f"[{self.name}] Extracted {len(results)} results")
                
            except Exception as e:
                logger.error(f"[{self.name}] Error: {e}")
            finally:
                browser.close()
        
        return results
```

**To use:** Add to `EngineManager` engines list as last fallback

---

### 7.3 Enhanced Logging (Optional)

**MODIFY:** `app/middleware/logging.py`

**REPLACE with structured logging:**

```python
"""Enhanced logging middleware with structured logs."""

import logging
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class EnhancedLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured request/response logging."""
    
    async def dispatch(self, request: Request, call_next):
        """Log request and response with correlation ID."""
        
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())[:8]
        request.state.correlation_id = correlation_id
        
        # Log request
        logger.info(
            f"[{correlation_id}] → {request.method} {request.url.path} "
            f"client={request.client.host if request.client else 'unknown'}"
        )
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        
        # Log response
        logger.info(
            f"[{correlation_id}] ← {response.status_code} "
            f"duration={duration_ms:.0f}ms"
        )
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response
```

---

## Summary

### Files to MODIFY
1. ✅ `requirements.txt` - Add scrapling
2. ✅ `app/engines/google.py` - Replace with Scrapling implementation
3. ✅ `app/engines/duckduckgo.py` - Replace with Scrapling implementation
4. ✅ `app/engines/manager.py` - Enhance fallback + circuit breaker
5. ✅ `app/config.py` - Add Scrapling settings, update version
6. ✅ `.env` - Update settings
7. ✅ `TECHNICAL_DOCUMENTATION.md` - Update status, architecture
8. ✅ `README.md` - Update features, version

### Files to CREATE
1. ✅ `test_scrapling_google.py` (temporary - delete after Phase 5)
2. ✅ `test_scrapling_duckduckgo.py` (temporary - delete after Phase 5)
3. ✅ `test_engines.py` (temporary - delete after Phase 5)
4. ✅ `CHANGELOG.md` (new)
5. ✅ `IMPLEMENTATION_PLAN.md` (this file)
6. ⚠️ `app/services/cache_service.py` (optional - Phase 7)
7. ⚠️ `app/engines/playwright_engine.py` (optional - Phase 7)

### Files to BACKUP (before modification)
1. ✅ `app/engines/google.old.py` (backup of google.py)
2. ✅ `app/engines/duckduckgo.old.py` (backup of duckduckgo.py)

### Files to DELETE (after validation)
1. ❌ `test_scrapling_google.py`
2. ❌ `test_scrapling_duckduckgo.py`
3. ❌ `test_engines.py`

### Files NOT MODIFIED (keep as-is)
- ✅ `app/engines/bing.py` - Already working
- ✅ `app/engines/base.py` - Interface unchanged
- ✅ `app/services/url_service.py` - URL extraction still needed for Bing
- ✅ `app/routes/search.py` - API interface unchanged
- ✅ `app/routes/health.py` - Works as-is (enhance in Phase 7 optional)
- ✅ `app/models/schemas.py` - Data models unchanged
- ✅ `main.py` - Entry point unchanged

---

## Estimated Timeline

- **Phase 0:** 15 minutes (install + test Scrapling)
- **Phase 1:** 20 minutes (Google engine migration)
- **Phase 2:** 20 minutes (DuckDuckGo engine migration)
- **Phase 3:** 15 minutes (Engine manager enhancement)
- **Phase 4:** 10 minutes (Configuration updates)
- **Phase 5:** 30 minutes (Testing & validation)
- **Phase 6:** 15 minutes (Documentation updates)
- **Phase 7:** 30-60 minutes (Optional enhancements)

**Total (minimum):** ~2 hours  
**Total (with optional):** ~3 hours

---

## Success Criteria

✅ All tests in Phase 5 pass  
✅ Google returns >5 results consistently  
✅ DuckDuckGo returns >5 results consistently  
✅ Bing still works  
✅ API response time <3 seconds  
✅ No errors on server startup  
✅ Fallback chain works correctly  
✅ Documentation updated  

---

## Rollback Plan

**If implementation fails:**

1. Restore backup files:
   ```bash
   cd scrapling-search-api/app/engines
   cp google.old.py google.py
   cp duckduckgo.old.py duckduckgo.py
   ```

2. Revert configuration changes in `config.py`

3. Uninstall Scrapling:
   ```bash
   pip uninstall scrapling
   ```

4. Restart server:
   ```bash
   uvicorn main:app --reload --port 8080
   ```

---

## Next Steps After Completion

1. **Monitor in production** for 1 week
2. **Track metrics:**
   - Success rate per engine
   - Response times
   - Cache hit rate (if implemented)
3. **Consider future enhancements:**
   - Add more engines (Yahoo, Yandex)
   - Implement result aggregation
   - Add API authentication
   - Deploy to cloud (VPS/Cloud Run)

---

**End of Implementation Plan**
