# Scrapling Migration Plan - Bing & Google Engines

**Date:** March 7, 2026  
**Goal:** Migrate Bing and Google engines to Scrapling to bypass bot detection

---

## 📁 **File Structure Plan**

```
app/engines/
├── base.py                    (unchanged)
├── bing.py                    (KEEP as backup - original httpx version)
├── bing_scrapling.py          (NEW - Scrapling Fetcher implementation)
├── google.py                  (KEEP as backup - original Playwright version)
├── google_scrapling.py        (NEW - Scrapling StealthyFetcher implementation)
├── duckduckgo.py              (existing - already working with Scrapling)
├── manager.py                 (unchanged)
└── __init__.py                (UPDATE - import new Scrapling versions)
```

---

## 🔧 **Implementation Details**

### **1. Bing Scrapling Implementation** (`bing_scrapling.py`)

#### Strategy:
- **Pattern:** Copy DuckDuckGo's proven approach (already working perfectly)
- **Fetcher:** `Fetcher()` from scrapling (curl_cffi-based, no JavaScript needed)
- **Confidence:** 95% success rate

#### Key Components:

**A. Initialization:**
```python
from scrapling import Fetcher

class BingEngine(BaseEngine):
    def __init__(self, settings):
        super().__init__(settings)
        self.fetcher = Fetcher()
        self.base_url = "https://www.bing.com/search"
```

**B. Search Method:**
- URL: `https://www.bing.com/search?q={query}`
- Retry logic: 3 attempts with exponential backoff
- HTTP status handling:
  - `200` → Parse results
  - `202/403` → Rate limited, wait 5s and retry
  - Other → Retry with delay

**C. Parsing (tested and confirmed working):**
- **Main selector:** `.b_algo` (returns `li` elements with search results)
- **Title extraction:**
  - Selector: `h2 a::text`
  - Fallback: `h2::text`
- **URL extraction:**
  - Selector: `h2 a::attr(href)` 
  - Get Bing redirect URL
  - Use existing `extract_bing_url()` from `url_service` to decode
- **Snippet extraction:**
  - Primary: `.b_caption p::text`
  - Fallback: `.b_caption::text`

**D. CSS Selector Syntax (Scrapling style):**
```python
# Getting elements
elements = page.css('.b_algo')

# Getting text
title = element.css('h2 a::text').get()

# Getting attribute
href = element.css('h2 a::attr(href)').get()
```

**E. Dependencies:**
- ✅ `scrapling` (already installed)
- ✅ `curl_cffi` (already installed)
- ✅ `extract_bing_url()` from `app.services.url_service`

---

### **2. Google Scrapling Implementation** (`google_scrapling.py`)

#### Strategy:
- **Pattern:** Use StealthyFetcher for JavaScript execution
- **Fetcher:** `StealthyFetcher()` from scrapling (Playwright-based with anti-bot)
- **Confidence:** 30% success rate (Google is very sophisticated)

#### Key Components:

**A. Initialization:**
```python
from scrapling import StealthyFetcher

class GoogleEngine(BaseEngine):
    def __init__(self, settings):
        super().__init__(settings)
        try:
            self.fetcher = StealthyFetcher()
            self.available = True
        except ImportError:
            logger.warning("[google] StealthyFetcher not available")
            self.available = False
```

**B. Search Method:**
- URL: `https://www.google.com/search?q={query}&num={limit}&hl=en`
- Use `.fetch(url)` which:
  - Launches headless browser
  - Executes JavaScript
  - Returns rendered page
- Retry logic: 3 attempts

**C. Parsing (Google's changing DOM):**
- **Try multiple selectors** (Google changes frequently):
  1. `div.g` (most common)
  2. `div[data-sokoban-container]`
  3. `div.Gx5Zad`
  4. `div#rso > div`

- **Title extraction:**
  - Primary: `h3::text`
  - Fallback: `[role="heading"]::text`
  - Alternative: `h3 > *::text`

- **URL extraction:**
  - Selector: `a::attr(href)`
  - Filter: Must start with `http`, exclude `google.com`
  - Handle Google redirect: `/url?q={actual_url}`

- **Snippet extraction:**
  - Try multiple selectors:
    - `div.VwiC3b::text`
    - `div[data-content-feature="1"]::text`
    - `span.aCOpRe::text`
    - `div.IsZvec::text`
    - `div[data-snf]::text`

**D. StealthyFetcher Features:**
- Playwright-based (executes JavaScript)
- Better browser fingerprinting than raw Playwright
- Randomized headers and timing
- Should avoid asyncio error (Scrapling handles async internally)

**E. Dependencies:**
- ✅ `scrapling` (already installed)
- ✅ `playwright` (already installed)
- ⚠️ **May need:** `patchright` (Playwright fork used by StealthyFetcher)
  - Check if StealthyFetcher works with standard Playwright first
  - Install `patchright` only if needed

---

### **3. Update `__init__.py`**

**Change imports from:**
```python
from app.engines.bing import BingEngine
from app.engines.google import GoogleEngine
```

**To:**
```python
from app.engines.bing_scrapling import BingEngine
from app.engines.google_scrapling import GoogleEngine
```

**Result:** 
- Old engines remain as `bing.py` and `google.py` (backup)
- Manager will automatically use new Scrapling versions
- No changes needed to `manager.py` or other code

---

## 📊 **Risk Assessment**

### Bing Scrapling Migration:
| Factor | Assessment | Notes |
|--------|-----------|-------|
| Success Probability | ✅ 95% | Same proven pattern as DuckDuckGo |
| Parsing Logic | ✅ Tested | Standalone test returned 10/10 results |
| Bot Detection Bypass | ✅ High | Scrapling's curl_cffi works for DDG |
| Breaking Changes | ✅ Low | Keeps existing `BingEngine` class name |
| Dependencies | ✅ All installed | No new packages needed |

### Google Scrapling Migration:
| Factor | Assessment | Notes |
|--------|-----------|-------|
| Success Probability | ⚠️ 30% | Google has sophisticated detection |
| JavaScript Execution | ✅ Supported | StealthyFetcher handles JS |
| Bot Detection Bypass | ⚠️ Uncertain | Better than raw Playwright, but not guaranteed |
| Async/Sync Issue | ✅ Fixed | Scrapling handles async internally |
| Dependencies | ⚠️ May need patchright | Check if works with standard Playwright |

---

## 🎯 **Implementation Order**

### Phase 1: Bing (High Priority, High Success)
1. Create `bing_scrapling.py`
2. Copy DuckDuckGo structure
3. Adapt selectors for Bing (`.b_algo`, `h2 a`, `.b_caption p`)
4. Test with standalone script first
5. Update `__init__.py` import
6. Test via API endpoint

**Expected Time:** 30 minutes  
**Success Rate:** 95%

### Phase 2: Google (Medium Priority, Low Success)
1. Create `google_scrapling.py`
2. Use StealthyFetcher pattern
3. Keep multiple selector attempts
4. Test with standalone script first
5. Update `__init__.py` import
6. Test via API endpoint

**Expected Time:** 1 hour  
**Success Rate:** 30%

### Phase 3: Dependency Check
- Test if StealthyFetcher works with existing packages
- If errors about `patchright`, install it:
  ```bash
  pip install patchright
  ```

---

## ✅ **Testing Strategy**

### Test Sequence:
1. **Standalone Script Test** (before integrating)
   - Create `test_bing_scrapling.py`
   - Create `test_google_scrapling.py`
   - Verify parsing works independently

2. **Integration Test** (after updating `__init__.py`)
   - Start API server
   - Test Bing: `GET /search?q=python&engine=bing&strict=true`
   - Test Google: `GET /search?q=python&engine=google&strict=true`

3. **Fallback Test**
   - Test automatic fallback chain
   - Verify DuckDuckGo still works

### Success Criteria:
- **Bing:** Returns 5+ results consistently
- **Google:** Either returns results OR fails gracefully (doesn't crash API)
- **Fallback:** If engines fail, falls back to working engines

---

## 🔄 **Rollback Plan**

If Scrapling versions fail:

1. **Quick rollback:**
   ```python
   # In __init__.py, change back to:
   from app.engines.bing import BingEngine
   from app.engines.google import GoogleEngine
   ```

2. **Keep both versions available:**
   ```python
   # Import both
   from app.engines.bing import BingEngine as BingHTTPX
   from app.engines.bing_scrapling import BingEngine as BingScrapling
   
   # Choose which to use
   BingEngine = BingScrapling  # or BingHTTPX
   ```

---

## 📝 **Code Style Guidelines**

1. **Docstrings:** Match DuckDuckGo's format
2. **Logging:** Use same logger format as existing engines
3. **Error Handling:** Try/except with informative messages
4. **Type Hints:** Include for all methods
5. **Comments:** Explain Bing/Google-specific logic

---

## 🚀 **Expected Outcome**

### Best Case (Bing + Google both work):
- ✅ 3/3 engines working with Scrapling
- ✅ Unified codebase (all use Scrapling)
- ✅ Better bot detection bypass across all engines
- ✅ No async/sync errors

### Likely Case (Bing works, Google fails):
- ✅ 2/3 engines working (DuckDuckGo + Bing)
- ⚠️ Google fails gracefully, falls back to others
- ✅ Production-ready with excellent fallback

### Worst Case (Bing fails):
- ✅ Quick rollback to original `bing.py`
- ✅ Still have DuckDuckGo working perfectly
- ℹ️ Can investigate Bing bot detection further

---

## 📦 **Deliverables**

1. ✅ `bing_scrapling.py` - New Bing implementation
2. ✅ `google_scrapling.py` - New Google implementation  
3. ✅ Updated `__init__.py` - Import new versions
4. ✅ Backup originals preserved (`bing.py`, `google.py`)
5. ✅ Testing scripts for validation
6. ✅ Documentation updates (if successful)

---

**Ready to implement?** The plan prioritizes Bing first (high success rate) before attempting Google (lower success rate but worth trying).
