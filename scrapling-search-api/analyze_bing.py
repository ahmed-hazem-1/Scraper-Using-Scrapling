"""
Extract and display first few Bing search results from the saved HTML.
"""
from lxml import html as lxml_html

def analyze_bing_html():
    """Parse the saved Bing HTML and extract search results."""
    
    with open('bing_response.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    tree = lxml_html.fromstring(html_content)
    
    # Find results
    result_elements = tree.cssselect('.b_algo')
    print(f"Found {len(result_elements)} results with '.b_algo' selector")
    print("=" * 80)
    
    for idx, elem in enumerate(result_elements[:3]):  # First 3 results
        print(f"\nResult #{idx + 1}:")
        print("-" * 80)
        
        # Try to extract title
        try:
            title_elems = elem.cssselect('h2 a')
            if title_elems:
                title = title_elems[0].text_content().strip()
                href = title_elems[0].get('href', '')
                print(f"Title (h2 a): {title}")
                print(f"Href: {href}")
            else:
                print("❌ No h2 a found")
        except Exception as e:
            print(f"❌ Error extracting title: {e}")
        
        # Try to extract caption
        try:
            caption_elems = elem.cssselect('.b_caption p')
            if caption_elems:
                snippet = caption_elems[0].text_content().strip()
                print(f"Snippet (.b_caption p): {snippet[:100]}...")
            else:
                print("❌ No .b_caption p found")
                
                # Try alternative
                caption_elems = elem.cssselect('.b_caption')
                if caption_elems:
                    snippet = caption_elems[0].text_content().strip()
                    print(f"Snippet (.b_caption): {snippet[:100]}...")
        except Exception as e:
            print(f"❌ Error extracting snippet: {e}")
        
        # Show element classes
        print(f"Element classes: {elem.get('class', 'N/A')}")
        
        # Show first 200 chars of inner HTML
        html_str = lxml_html.tostring(elem, encoding='unicode')
        print(f"\nFirst 300 chars of HTML:")
        print(html_str[:300])
        print("...")


if __name__ == "__main__":
    analyze_bing_html()
