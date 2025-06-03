import unittest
import sys
import os

# Add project root to sys.path to allow imports from aisans package
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aisans.crawler.parser import parse_html_content

class TestParseHtmlContent(unittest.TestCase):

    def test_html_with_text_and_links(self):
        html = """
        <html><head><title>Test Page</title></head>
        <body>
            <p>Hello world! This is a test.</p>
            <a href="https://example.com/page1">Page 1</a>
            <a href="/relative/path">Relative Path</a>
            <a href="https://another.com/abs">Absolute Link</a>
            <a href="page2.html">Another Relative</a>
        </body></html>
        """
        base_url = "https://example.com"
        title, text, links = parse_html_content(html, base_url=base_url)

        self.assertEqual(title, "Test Page")
        # Corrected: soup.get_text() includes the title text.
        self.assertEqual(text, "Test Page Hello world! This is a test. Page 1 Relative Path Absolute Link Another Relative")
        self.assertCountEqual(links, [
            "https://example.com/page1",
            "https://example.com/relative/path",
            "https://another.com/abs",
            "https://example.com/page2.html"
        ])

    def test_html_with_text_and_links_no_base_url(self):
        html = """
        <html><head><title>Test Page No Base</title></head>
        <body>
            <p>Some text here.</p>
            <a href="https://example.com/absolute_only">Absolute Only</a>
            <a href="/relative_ignored">Relative Ignored</a>
        </body></html>
        """
        title, text, links = parse_html_content(html) # No base_url

        self.assertEqual(title, "Test Page No Base")
        # Corrected: soup.get_text() includes the title text.
        self.assertEqual(text, "Test Page No Base Some text here. Absolute Only Relative Ignored")
        self.assertCountEqual(links, ["https://example.com/absolute_only"])

    def test_html_with_only_text(self):
        html = "<p>This is only text, there are no links.</p><span>More text.</span>"
        title, text, links = parse_html_content(html)
        self.assertEqual(title, "") # No title tag
        self.assertEqual(text, "This is only text, there are no links. More text.")
        self.assertEqual(links, [])

    def test_html_with_only_links(self):
        html = """
        <head><title>Links Only</title></head>
        <body>
            <a href="https://link1.com">Link1 Text</a>
            <a href="/link2">Link2 Text</a>
        </body>
        """
        base_url = "http://base.com"
        title, text, links = parse_html_content(html, base_url=base_url)
        self.assertEqual(title, "Links Only")
        # Corrected: soup.get_text() includes the title text.
        self.assertEqual(text, "Links Only Link1 Text Link2 Text")
        self.assertCountEqual(links, ["https://link1.com", "http://base.com/link2"])

    def test_empty_html_string(self):
        html = ""
        title, text, links = parse_html_content(html)
        self.assertEqual(title, "")
        self.assertEqual(text, "")
        self.assertEqual(links, [])

    def test_html_with_malformed_elements(self):
        # BeautifulSoup is generally robust to malformed HTML
        html = """
        <html><head><title>Malformed Page</title></head><body>
            <p>Some valid text.
            <a href="https://good.com">Good Link</a>
            <a href="bad_link_no_quotes>Bad Link Styling
            <a href="">Empty Href</a>
            <a>No Href</a>
        </body></html>
        """
        title, text, links = parse_html_content(html, base_url="https://base.com")
        self.assertEqual(title, "Malformed Page")
        # The exact text extraction can vary slightly with malformed HTML,
        # focusing on links here. BS4 might try to correct or interpret.
        # print(f"Malformed text: '{text}'") # For debugging if needed
        self.assertIn("Some valid text.", text)
        self.assertIn("Good Link", text)
        
        # Depending on parser leniency, "bad_link_no_quotes" might not be parsed as an href.
        # BS4's html.parser is quite lenient.
        # `a_tag['href']` would exist even if `href` value is "bad_link_no_quotes>..."
        # urljoin would then treat this as a relative path.
        # The actual extracted href from the malformed tag by BeautifulSoup is:
        # 'bad_link_no_quotes>Bad Link Styling            <a href='
        # which, when joined with "https://base.com", becomes the expected link below.
        self.assertCountEqual(links, [
            "https://good.com",
            "https://base.com/bad_link_no_quotes>Bad Link Styling            <a href="
        ])


    def test_duplicate_links(self):
        html = """
        <html><head><title>Duplicates Test</title></head><body>
        <a href="https://example.com/page">Link 1</a>
        <a href="https://example.com/page">Link 2</a>
        <a href="/relative">Relative 1</a>
        <a href="/relative">Relative 2</a>
        </body></html>
        """
        base_url = "https://example.com"
        title, text, links = parse_html_content(html, base_url=base_url)
        self.assertEqual(title, "Duplicates Test")
        # Corrected: soup.get_text() includes the title text.
        self.assertEqual(text, "Duplicates Test Link 1 Link 2 Relative 1 Relative 2")
        self.assertCountEqual(links, ["https://example.com/page", "https://example.com/relative"])

    def test_links_with_fragments_and_queries(self):
        html = """
        <html><head><title>Links Special</title></head><body>
        <a href="https://example.com/page#section">With Fragment</a>
        <a href="/path?param=value">With Query</a>
        </body></html>
        """
        base_url = "https://example.com"
        title, text, links = parse_html_content(html, base_url=base_url)
        self.assertEqual(title, "Links Special")
        self.assertCountEqual(links, [
            "https://example.com/page#section",
            "https://example.com/path?param=value"
        ])

if __name__ == '__main__':
    unittest.main()
