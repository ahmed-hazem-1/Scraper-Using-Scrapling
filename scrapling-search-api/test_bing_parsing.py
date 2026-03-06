"""
Complete test of Bing parsing using the actual engine code logic.
"""
import sys
sys.path.insert(0, 'D:\\Trendy\\Scraper\\scrapling-search-api')

from lxml import html as lxml_html
from app.services.url_service import extract_bing_url, is_valid_search_result_url
from app.models.schemas import SearchResult

def test_bing_parsing():
    """Test the complete Bing parsing logic."""
    
    with open('bing_response.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    tree = lxml_html.fromstring(html_content)
    result_elements = tree.cssselect('.b_algo')
    
    print(f"Found {len(result_elements)} .b_algo elements")
    print("=" * 80)
    
    results = []
    max_results = 10
    
    for idx, elem in enumerate(result_elements):
        if len(results) >= max_results:
            break
        
        print(f"\n{'─' * 80}")
        print(f"Processing Result #{idx + 1}")
        print('─' * 80)
        
        try:
            # Extract title and URL from h2 > a
            title_elems = elem.cssselect('h2 a')
            print(f"h2 a elements found: {len(title_elems)}")
            
            if not title_elems:
                print("❌ No title elements, skipping")
                continue
            
            title = title_elems[0].text_content().strip()
            bing_redirect_url = title_elems[0].get('href', '')
            
            print(f"Title: {title}")
            print(f"Bing redirect URL: {bing_redirect_url[:80]}...")
            
            # Extract actual URL from Bing redirect
            url = extract_bing_url(bing_redirect_url)
            print(f"Extracted URL: {url}")
            
            # Extract snippet from .b_caption p
            snippet_elems = elem.cssselect('.b_caption p')
            snippet = snippet_elems[0].text_content().strip() if snippet_elems else ""
            print(f"Snippet (first 100 chars): {snippet[:100]}")
            
            # Validate
            if not title:
                print("❌ REJECTED: No title")
                continue
                
            if not is_valid_search_result_url(url):
                print(f"❌ REJECTED: Invalid URL: {url}")
                continue
            
            print(f"✅ ACCEPTED")
            
            results.append(SearchResult(
                title=title,
                snippet=snippet,
                url=url
            ))
            
        except Exception as e:
            print(f"❌ ERROR parsing result {idx}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("\n" + "=" * 80)
    print(f"FINAL RESULTS: {len(results)} items")
    print("=" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"\n#{i}:")
        print(f"  Title: {result.title}")
        print(f"  URL: {result.url}")
        print(f"  Snippet: {result.snippet[:80]}...")


if __name__ == "__main__":
    test_bing_parsing()
