"""
Test Bing URL extraction with actual URLs from the saved HTML.
"""
import base64
from urllib.parse import urlparse, parse_qs

def extract_bing_url_test(bing_url: str) -> str:
    """Test extraction of actual URL from Bing redirect."""
    print(f"Input URL: {bing_url[:100]}...")
    print("-" * 80)
    
    try:
        # Parse the URL
        parsed = urlparse(bing_url)
        print(f"Parsed path: {parsed.path}")
        print(f"Parsed query: {parsed.query[:100]}...")
        
        params = parse_qs(parsed.query)
        print(f"Query params keys: {list(params.keys())}")
        
        # Extract the 'u' parameter
        if 'u' in params:
            encoded_value = params['u'][0]
            print(f"Encoded value: {encoded_value}")
            print(f"Length: {len(encoded_value)}")
            
            # Remove prefix
            if len(encoded_value) > 2:
                base64_part = encoded_value[2:]
                print(f"Base64 part (after removing prefix): {base64_part}")
                
                # Add padding
                missing_padding = len(base64_part) % 4
                if missing_padding:
                    base64_part += '=' * (4 - missing_padding)
                    print(f"Added padding: {missing_padding} chars")
                
                print(f"Final base64 string: {base64_part}")
                
                # Decode
                try:
                    decoded_bytes = base64.b64decode(base64_part)
                    actual_url = decoded_bytes.decode('utf-8')
                    print(f"✅ DECODED URL: {actual_url}")
                    return actual_url
                except Exception as e:
                    print(f"❌ Decode error: {e}")
        else:
            print("❌ No 'u' parameter found!")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return bing_url


# Test with actual URLs from analysis
test_urls = [
    # Result 1 (Chinese)
    "https://www.bing.com/ck/a?!&&p=f14b8da625c72cd0e87b4bb835051b36002c75429e77852eb6e1d789540e2728JmltdHM9MTc3Mjc1NTIwMA&ptn=3&ver=2&hsh=4&fclid=024101d4-3e2e-6743-0c6a-16c03f526653&u=a1aHR0cHM6Ly93d3cuemhpaHUuY29tL3F1ZXN0aW9uLzI5MTM4MDIw&ntb=1",
    
    # Result 2 (Stack Overflow)
    "https://www.bing.com/ck/a?!&&p=d17865126c65ed7886eb6e71788534cf4ef960082a67c582ba01df95786b549fJmltdHM9MTc3Mjc1NTIwMA&ptn=3&ver=2&hsh=4&fclid=024101d4-3e2e-6743-0c6a-16c03f526653&u=a1aHR0cHM6Ly9zdGFja292ZXJmbG93LmNvbS9xdWVzdGlvbnMvMjYwMDAxOTgvd2hhdC1kb2VzLWNvbG9uLWVxdWFsLWluLXB5dGhvbi1tZWFu&ntb=1",
]

for i, url in enumerate(test_urls, 1):
    print(f"\n{'=' * 80}")
    print(f"TEST #{i}")
    print('=' * 80)
    result = extract_bing_url_test(url)
    print()
