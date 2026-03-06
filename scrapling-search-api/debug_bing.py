"""
Debug script to check Bing's HTML response and identify why parsing is failing.
"""
import httpx
from lxml import html as lxml_html

def test_bing():
    """Test Bing search and analyze HTML structure."""
    
    query = "python"
    search_url = f"https://www.bing.com/search?q={query}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    print(f"Fetching: {search_url}")
    print("=" * 80)
    
    with httpx.Client(timeout=30) as client:
        response = client.get(search_url, headers=headers, follow_redirects=True)
        print(f"Status Code: {response.status_code}")
        print(f"Response URL: {response.url}")
        print(f"HTML Length: {len(response.text)} characters")
        print("=" * 80)
        
        # Save HTML to file for inspection
        with open('bing_response.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"✅ HTML saved to: bing_response.html")
        print("=" * 80)
        
        # Parse and check for expected selectors
        tree = lxml_html.fromstring(response.text)
        
        # Check various selectors
        selectors = [
            '.b_algo',           # Original selector
            'li.b_algo',         # With li tag
            '.b_algo h2',        # h2 inside b_algo
            'ol#b_results li',   # Alternative
            '[data-bm]',         # Data attribute
            'h2 a',              # Direct title links
        ]
        
        print("Testing CSS Selectors:")
        print("-" * 80)
        for selector in selectors:
            try:
                elements = tree.cssselect(selector)
                print(f"{selector:30} → Found {len(elements)} elements")
                
                if elements and len(elements) > 0:
                    # Show first result details
                    first = elements[0]
                    print(f"  First element tag: {first.tag}")
                    print(f"  First element classes: {first.get('class', 'N/A')}")
                    print(f"  First element text (first 100 chars): {first.text_content()[:100]}")
            except Exception as e:
                print(f"{selector:30} → ERROR: {e}")
        
        print("=" * 80)
        
        # Check for bot detection indicators
        bot_indicators = [
            '<title>',
            'captcha',
            'robot',
            'unusual traffic',
            'security',
            'cookie',
        ]
        
        html_lower = response.text.lower()
        print("Bot Detection Indicators:")
        print("-" * 80)
        for indicator in bot_indicators:
            if indicator in html_lower:
                # Find context around the indicator
                idx = html_lower.find(indicator)
                context = response.text[max(0, idx-50):idx+50]
                print(f"✓ Found '{indicator}': ...{context}...")
        
        print("=" * 80)


if __name__ == "__main__":
    test_bing()
