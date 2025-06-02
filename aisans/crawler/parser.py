from bs4 import BeautifulSoup
from urllib.parse import urljoin

def parse_html_content(html_content: str, base_url: str | None = None) -> tuple[str, list[str]]:
    """
    Parses HTML content to extract text and hyperlinks.

    Args:
        html_content: The HTML content as a string.
        base_url: Optional base URL to resolve relative links.

    Returns:
        A tuple containing:
            - The extracted text (as a single string).
            - A list of unique absolute URLs (as strings).
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract text content
    text_content = soup.get_text(separator=' ', strip=True)

    # Extract hyperlinks
    extracted_links = set()
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if not href:
            continue

        # Check if the link is absolute
        if href.startswith('http://') or href.startswith('https://'):
            extracted_links.add(href)
        elif base_url:
            absolute_link = urljoin(base_url, href)
            extracted_links.add(absolute_link)

    return text_content, list(extracted_links)

if __name__ == '__main__':
    sample_html_with_base = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <p>This is some sample text.
                It has a <a href="https://www.example.com/absolute">link</a>.
            </p>
            <p>Another paragraph with a <a href="/relative/path">relative link</a>.</p>
            <a href="another_absolute.html">Another absolute link relative to base</a>
            <a href="https://www.anotherdomain.com/page">External Link</a>
            <a href="">Empty Link</a>
            <a>No Href Link</a>
        </body>
    </html>
    """
    base = "https://www.example.com"
    text, links = parse_html_content(sample_html_with_base, base_url=base)
    print(f"--- Parsing with base_url: {base} ---")
    print("Extracted Text:")
    print(text)
    print("\nExtracted Links:")
    for link in links:
        print(link)

    print("-" * 30)

    sample_html_no_base = """
    <html>
        <body>
            <p>Text with <a href="https://www.absolute.com/page1">absolute link</a>.</p>
            <p>Text with <a href="/relative/page2">relative link (will be ignored)</a>.</p>
        </body>
    </html>
    """
    text_no_base, links_no_base = parse_html_content(sample_html_no_base)
    print("--- Parsing without base_url ---")
    print("Extracted Text:")
    print(text_no_base)
    print("\nExtracted Links:")
    for link in links_no_base:
        print(link)

    # Test with empty html
    empty_html = ""
    text_empty, links_empty = parse_html_content(empty_html, base_url="https://example.com")
    print("\n--- Parsing empty HTML ---")
    print(f"Text: '{text_empty}'")
    print(f"Links: {links_empty}")

    # Test with html having only text
    html_only_text = "<p>Just some text, no links.</p>"
    text_only, links_only = parse_html_content(html_only_text)
    print("\n--- Parsing HTML with only text ---")
    print(f"Text: '{text_only}'")
    print(f"Links: {links_only}")

    # Test with html having only links
    html_only_links = '<a href="https://link1.com">1</a> <a href="/link2">2</a>'
    text_l, links_l_no_base = parse_html_content(html_only_links)
    print("\n--- Parsing HTML with only links (no base_url) ---")
    print(f"Text: '{text_l}'") # Should be "1 2" or similar
    print(f"Links: {links_l_no_base}")


    text_l_base, links_l_base = parse_html_content(html_only_links, base_url="https_//example.com")
    print("\n--- Parsing HTML with only links (with base_url) ---")
    print(f"Text: '{text_l_base}'") # Should be "1 2" or similar
    print(f"Links: {links_l_base}")
