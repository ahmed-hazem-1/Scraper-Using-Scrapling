from scrapling import Fetcher
import urllib.parse

fetcher = Fetcher()
page = fetcher.get('https://html.duckduckgo.com/html/?' + urllib.parse.urlencode({'q': 'python 2026'}))

# Get first result element
results = page.css('div.result')
if results:
    first = results[0]
    print("=" * 80)
    print("FIRST RESULT HTML:")
    print("=" * 80)
    # Get HTML using get() method and string representation
    print(str(first.get())[:2000])
    print("\n" + "=" * 80)
    print("ALL SELECTORS:")
    print("=" * 80)
    
    # Test various selectors
    print(f"Title: {first.css('a.result__a::text').get()}")
    print(f"URL: {first.css('a.result__a::attr(href)').get()}")
    
    # Try different snippet selectors
    snippet1 = first.css('a.result__snippet::text').get()
    snippet2 = first.css('a.result__snippet').get()
    
    if snippet2:
        # Get all text from snippet element
        snippet_texts = first.css('a.result__snippet *::text').getall()
        snippet_full = ' '.join([t.strip() for t in snippet_texts if t.strip()])
        print(f"Snippet (full): {snippet_full}")
    
    print(f"Snippet (method1): {snippet1}")
    
    # Look for date/timestamp
    date_selectors = [
        'span.result__timestamp::text',
        'span.timestamp::text', 
        'time::text',
        'time::attr(datetime)',
        'span.result__date::text',
        '.result__extras span::text'
    ]
    
    print("\n" + "=" * 80)
    print("DATE SEARCH:")
    print("=" * 80)
    for sel in date_selectors:
        val = first.css(sel).get()
        if val:
            print(f"Found with {sel}: {val}")
    
    # Look for additional content
    print("\n" + "=" * 80)
    print("ALL TEXT IN RESULT:")
    print("=" * 80)
    all_text = first.css('*::text').getall()
    for i, text in enumerate(all_text[:15]):
        if text.strip():
            print(f"{i}: {text.strip()}")
