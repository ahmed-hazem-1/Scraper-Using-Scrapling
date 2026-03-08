"""
Search engine manager with automatic fallback.

Manages multiple search engines and provides automatic fallback
if one engine fails or hits a rate limit.
"""

from typing import List, Optional
from app.config import get_logger, Settings
from app.models.schemas import SearchResult
from app.engines.base import BaseEngine
from app.engines.duckduckgo import DuckDuckGoEngine
from app.engines.bing_scrapling import BingEngine
from app.engines.google import GoogleEngine

logger = get_logger(__name__)


class EngineManager:
    """
    Manager for multiple search engines with automatic fallback.
    
    Tries engines in order until one succeeds. If an engine is rate limited
    or fails, automatically falls back to the next one.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize the engine manager.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        
        # Initialize all available engines in priority order
        # Note: GoogleEngine removed - doesn't work in async context (Playwright sync API issue)
        self.engines: List[BaseEngine] = [
            DuckDuckGoEngine(settings),  # Primary: Best accuracy, bypasses bot detection
            BingEngine(settings),        # Backup: Works but may return generic results
        ]

        # Circuit-breaker state: track consecutive failures per engine
        self.engine_failures = {engine.name: 0 for engine in self.engines}
        self.engine_disabled_until = {engine.name: 0.0 for engine in self.engines}

        engine_names = [e.name for e in self.engines]
        logger.info(f"EngineManager initialized with engines: {engine_names}")
    
    def search(
        self, 
        query: str, 
        limit: int,
        preferred_engine: Optional[str] = None,
        strict_mode: bool = False,
        year: Optional[int] = None
    ) -> tuple[List[SearchResult], str]:
        """
        Search using available engines with automatic fallback.
        
        Tries engines in order until one succeeds. Returns results
        along with the name of the engine that was used.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            preferred_engine: Optional engine name to try first
            strict_mode: If True, only try the preferred engine (no fallback)
            year: Optional year to filter results by
        
        Returns:
            tuple: (list of results, engine name used)
        
        Raises:
            Exception: If all engines fail (or if strict_mode and preferred engine fails)
        """
        logger.info(f"EngineManager searching: query='{query}', limit={limit}")
        
        # Reorder engines if preferred engine is specified
        engines_to_try = self._get_engine_order(preferred_engine)
        
        # In strict mode, only try the first engine (preferred)
        if strict_mode and preferred_engine:
            engines_to_try = [engines_to_try[0]]
            logger.info(f"Strict mode enabled: only trying {engines_to_try[0].name}")
        
        last_error = None
        
        import time as _time
        for engine in engines_to_try:
            if self._is_engine_disabled(engine.name):
                logger.warning(f"Skipping {engine.name}: circuit breaker open")
                continue
            try:
                logger.info(f"Trying engine: {engine.name}")

                results = engine.search(query, limit, year=year)

                if len(results) == 0:
                    logger.warning(f"{engine.name} returned no results, trying next engine...")
                    self._record_failure(engine.name)
                    continue

                # Success — reset failure counter
                self.engine_failures[engine.name] = 0
                logger.info(f"Search successful using {engine.name}: {len(results)} results")
                return results, engine.name

            except Exception as e:
                last_error = e
                logger.warning(f"{engine.name} failed: {e}, trying next engine...")
                self._record_failure(engine.name)
                continue

        # All engines failed
        error_msg = f"All search engines failed. Last error: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    def _record_failure(self, engine_name: str) -> None:
        """Increment failure count; disable engine temporarily after 3 consecutive failures."""
        import time as _time
        self.engine_failures[engine_name] = self.engine_failures.get(engine_name, 0) + 1
        if self.engine_failures[engine_name] >= 3:
            disable_secs = 300  # 5 minutes
            self.engine_disabled_until[engine_name] = _time.time() + disable_secs
            logger.warning(f"{engine_name}: 3 consecutive failures — disabling for {disable_secs}s")

    def _is_engine_disabled(self, engine_name: str) -> bool:
        """Return True if the engine is currently in the circuit-breaker cooldown."""
        import time as _time
        until = self.engine_disabled_until.get(engine_name, 0.0)
        if _time.time() < until:
            return True
        # Cooldown expired — reset
        if until > 0:
            self.engine_failures[engine_name] = 0
            self.engine_disabled_until[engine_name] = 0.0
            logger.info(f"{engine_name}: circuit breaker reset")
        return False

    def _get_engine_order(self, preferred_engine: Optional[str] = None) -> List[BaseEngine]:
        """
        Get engines in order to try, with preferred engine first if specified.
        
        Args:
            preferred_engine: Optional engine name to prioritize
        
        Returns:
            List[BaseEngine]: Ordered list of engines to try
        """
        logger.debug(f"_get_engine_order called with preferred_engine={preferred_engine}")
        logger.debug(f"Available engines: {[e.name for e in self.engines]}")
        
        if not preferred_engine:
            logger.debug("No preferred engine, using default order")
            return self.engines
        
        # Find preferred engine and move it to front
        preferred = None
        others = []
        
        for engine in self.engines:
            logger.debug(f"Comparing: engine.name='{engine.name}', engine.name.lower()='{engine.name.lower()}', preferred_engine.lower()='{preferred_engine.lower()}'")
            if engine.name.lower() == preferred_engine.lower():
                preferred = engine
                logger.debug(f"Found matching engine: {engine.name}")
            else:
                others.append(engine)
        
        if preferred:
            ordered = [preferred] + others
            logger.info(f"Reordered engines: {[e.name for e in ordered]}")
            return ordered
        else:
            logger.warning(f"Preferred engine '{preferred_engine}' not found, using default order")
            return self.engines
    
    def get_available_engines(self) -> List[str]:
        """
        Get list of available engine names.
        
        Returns:
            List[str]: List of engine names
        """
        return [engine.name for engine in self.engines]
