"""
URL manipulation and extraction utilities.

This module provides functions for:
- Extracting actual URLs from search engine redirect links (DuckDuckGo, Bing, Google)
- URL validation
- URL normalization
- Domain extraction and matching
"""

import base64
from urllib.parse import urlparse, parse_qs, unquote
from typing import Optional, List
from app.config import get_logger

logger = get_logger(__name__)


def extract_actual_url(ddg_url: str) -> str:
    """
    Extract the actual target URL from a DuckDuckGo redirect URL.
    
    DuckDuckGo uses redirect URLs with the pattern:
    //duckduckgo.com/l/?uddg={encoded_url}&rut={token}
    
    This function extracts and decodes the original URL from the 'uddg' parameter.
    
    Args:
        ddg_url: DuckDuckGo redirect URL
    
    Returns:
        str: The actual target URL, or original URL if extraction fails
    
    Examples:
        >>> url = "//duckduckgo.com/l/?uddg=https%3A%2F%2Fwww.python.org%2F"
        >>> extract_actual_url(url)
        'https://www.python.org/'
    """
    try:
        # Add https: scheme if URL starts with //
        if ddg_url.startswith('//'):
            ddg_url = 'https:' + ddg_url
        
        # Parse the URL and extract query parameters
        parsed = urlparse(ddg_url)
        params = parse_qs(parsed.query)
        
        # Extract and decode the 'uddg' parameter
        if 'uddg' in params and params['uddg']:
            actual_url = unquote(params['uddg'][0])
            logger.debug(f"Extracted URL: {actual_url} from {ddg_url[:50]}...")
            return actual_url
        
        # If no uddg parameter, return original
        logger.warning(f"Could not find 'uddg' parameter in URL: {ddg_url[:50]}...")
        return ddg_url
        
    except Exception as e:
        logger.warning(f"Failed to extract URL from {ddg_url[:50]}...: {e}")
        return ddg_url


def extract_bing_url(bing_url: str) -> str:
    """
    Extract the actual target URL from a Bing redirect URL.
    
    Bing uses redirect URLs with the pattern:
    https://www.bing.com/ck/a?!&&p=...&u=a1{base64_encoded_url}&ntb=1
    
    This function extracts and decodes the original URL from the 'u' parameter.
    The 'u' parameter contains a base64-encoded URL with a prefix (e.g., 'a1').
    
    Args:
        bing_url: Bing redirect URL
    
    Returns:
        str: The actual target URL, or original URL if extraction fails
    
    Examples:
        >>> url = "https://www.bing.com/ck/a?u=a1aHR0cHM6Ly93d3cucHl0aG9uLm9yZy8"
        >>> extract_bing_url(url)
        'https://www.python.org/'
    """
    try:
        # Parse the URL and extract query parameters
        parsed = urlparse(bing_url)
        params = parse_qs(parsed.query)
        
        # Extract the 'u' parameter
        if 'u' in params and params['u']:
            encoded_value = params['u'][0]
            logger.debug(f"Bing URL encoded value: {encoded_value[:50]}...")
            
            # Remove the prefix (usually 'a1' or similar)
            # The actual base64 starts after the first 2 characters
            if len(encoded_value) > 2:
                base64_part = encoded_value[2:]
                
                # Add padding if needed (base64 strings must be multiples of 4)
                missing_padding = len(base64_part) % 4
                if missing_padding:
                    base64_part += '=' * (4 - missing_padding)
                
                # Try to decode
                try:
                    decoded_bytes = base64.b64decode(base64_part)
                    actual_url = decoded_bytes.decode('utf-8')
                    logger.debug(f"Extracted Bing URL: {actual_url}")
                    return actual_url
                except Exception as decode_error:
                    logger.debug(f"Failed to decode Bing URL: {decode_error}")
        else:
            logger.debug(f"No 'u' parameter found in Bing URL: {bing_url[:100]}")
        
        # If Bing redirect extraction fails, return original
        return bing_url
        
    except Exception as e:
        logger.warning(f"Failed to extract Bing URL from {bing_url[:50]}...: {e}")
        return bing_url


def extract_google_url(google_url: str) -> str:
    """
    Extract the actual target URL from a Google redirect URL.
    
    Google may use redirect URLs with patterns like:
    - https://www.google.com/url?q={encoded_url}&sa=...
    - Direct URLs without redirection
    
    This function extracts the original URL from the 'q' parameter if present.
    
    Args:
        google_url: Google redirect URL or direct URL
    
    Returns:
        str: The actual target URL, or original URL if no extraction needed
    
    Examples:
        >>> url = "https://www.google.com/url?q=https%3A%2F%2Fwww.python.org%2F"
        >>> extract_google_url(url)
        'https://www.python.org/'
    """
    try:
        # Check if it's a Google redirect URL
        if 'google.com/url' in google_url:
            parsed = urlparse(google_url)
            params = parse_qs(parsed.query)
            
            # Extract and decode the 'q' parameter
            if 'q' in params and params['q']:
                actual_url = unquote(params['q'][0])
                logger.debug(f"Extracted Google URL: {actual_url}")
                return actual_url
        
        # If not a redirect or no 'q' parameter, return original
        return google_url
        
    except Exception as e:
        logger.warning(f"Failed to extract Google URL from {google_url[:50]}...: {e}")
        return google_url


def validate_url(url: str) -> bool:
    """
    Validate if a URL is properly formed and uses HTTP/HTTPS.
    
    Args:
        url: URL string to validate
    
    Returns:
        bool: True if URL is valid, False otherwise
    
    Examples:
        >>> validate_url("https://www.python.org")
        True
        >>> validate_url("not a url")
        False
    """
    try:
        parsed = urlparse(url)
        return parsed.scheme in ('http', 'https') and bool(parsed.netloc)
    except Exception as e:
        logger.debug(f"URL validation failed for {url[:50]}...: {e}")
        return False


def normalize_url(url: str) -> str:
    """
    Normalize a URL by ensuring it has a scheme and cleaning formatting.
    
    Args:
        url: URL string to normalize
    
    Returns:
        str: Normalized URL
    
    Examples:
        >>> normalize_url("//example.com/path")
        'https://example.com/path'
        >>> normalize_url("example.com")
        'https://example.com'
    """
    url = url.strip()
    
    # Add https:// for protocol-relative URLs
    if url.startswith('//'):
        return 'https:' + url
    
    # Add https:// if no scheme present
    if not url.startswith(('http://', 'https://')):
        return 'https://' + url
    
    return url


def is_valid_search_result_url(url: str) -> bool:
    """
    Check if a URL is valid for inclusion in search results.
    
    This performs more strict validation than validate_url, ensuring:
    - URL starts with http:// or https://
    - URL is not empty or just whitespace
    - URL is not a DuckDuckGo internal link
    
    Args:
        url: URL to check
    
    Returns:
        bool: True if URL should be included in results
    """
    if not url or not url.strip():
        return False
    
    url = url.strip()
    
    # Must start with http:// or https://
    if not url.startswith(('http://', 'https://')):
        return False
    
    # Skip DuckDuckGo internal links
    if 'duckduckgo.com' in url and '/l/?' not in url:
        return False
    
    return validate_url(url)


def extract_domain(url: str) -> str:
    """
    Extract the domain name from a URL.
    
    Removes protocol, www prefix, and path to get clean domain.
    
    Args:
        url: Full URL string
    
    Returns:
        str: Domain name (e.g., "python.org")
    
    Examples:
        >>> extract_domain("https://www.python.org/docs/")
        'python.org'
        >>> extract_domain("http://github.com")
        'github.com'
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain
    except Exception as e:
        logger.debug(f"Failed to extract domain from {url[:50]}...: {e}")
        return ""


def matches_sources(url: str, sources: List[str]) -> bool:
    """
    Check if a URL's domain matches any of the specified source domains.
    
    Performs case-insensitive matching and handles www prefix automatically.
    Supports subdomain matching (e.g., "wikipedia.org" matches "en.wikipedia.org").
    
    Args:
        url: URL to check
        sources: List of domain names to match against
    
    Returns:
        bool: True if URL domain matches any source
    
    Examples:
        >>> matches_sources("https://www.python.org/docs", ["python.org"])
        True
        >>> matches_sources("https://en.wikipedia.org/wiki/Python", ["wikipedia.org"])
        True
        >>> matches_sources("https://github.com", ["python.org", "github.com"])
        True
        >>> matches_sources("https://example.com", ["python.org"])
        False
    """
    if not sources:
        return True  # No filter means all sources are valid
    
    url_domain = extract_domain(url)
    if not url_domain:
        return False
    
    # Normalize source domains (remove www, convert to lowercase)
    normalized_sources = []
    for source in sources:
        source = source.lower().strip()
        if source.startswith('www.'):
            source = source[4:]
        normalized_sources.append(source)
    
    # Check for exact match first
    if url_domain in normalized_sources:
        return True
    
    # Check for subdomain match (e.g., en.wikipedia.org matches wikipedia.org)
    for source in normalized_sources:
        if url_domain.endswith('.' + source):
            return True
    
    return False
