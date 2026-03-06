"""Debug script to check Bing Scrapling HTML structure"""

from scrapling import Fetcher
from urllib.parse import quote_plus

query = "Ahmed Hazem Elabady"
url = f"https://www.bing.com/search?q={quote_plus(query)}&setlang=en-US&mkt=en-US"

print(f"Testing URL: {url}\n")

fetcher = Fetcher()
page = fetcher.get(url)

print(f"Status: {page.status}")

# Check for result elements
results = page.css('.b_algo')
print(f"Found {len(results)} .b_algo elements\n")

if results:
    first = results[0]
    print("=== First Result Structure ===\n")
    
    # Try different title selectors
    print("Title attempts:")
    print(f"  h2 a::text = '{first.css('h2 a::text').get()}'")
    print(f"  h2::text = '{first.css('h2::text').get()}'")
    print(f"  a::text (first) = '{first.css('a::text').get()}'")
    
    # Check attributes
    print(f"\n  h2 a::attr(aria-label) = '{first.css('h2 a::attr(aria-label)').get()}'")
    print(f"  h2 a::attr(title) = '{first.css('h2 a::attr(title)').get()}'")
    print(f"  h2 a::attr(h) = '{first.css('h2 a::attr(h)').get()}'")
    
    print(f"\nURL: {first.css('h2 a::attr(href)').get()}")
    print(f"Snippet: {first.css('.b_caption p::text').get()}")
