import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to sys.path to allow imports from aisans package
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aisans.crawler.crawler import fetch_url_content, robot_parsers_cache, CRAWLER_USER_AGENT
import requests # For requests.exceptions

# Helper for mock requests.get side_effect
def mock_requests_get_side_effect_handler(robots_txt_content, page_content, page_status_code=200, robots_status_code=200, robots_error=None, page_error=None):
    def side_effect_func(url, headers, timeout):
        mock_resp = MagicMock()
        mock_resp.url = url # Store URL in mock_resp for debugging if needed
        if "robots.txt" in url:
            if robots_error:
                raise robots_error
            mock_resp.status_code = robots_status_code
            mock_resp.text = robots_txt_content if robots_status_code == 200 else ""
            # print(f"Mocking robots.txt fetch for {url}: status={mock_resp.status_code}, content='{mock_resp.text[:30]}...'")
        else: # Actual page URL
            if page_error:
                raise page_error
            mock_resp.status_code = page_status_code
            mock_resp.text = page_content if page_status_code == 200 else ""
            # print(f"Mocking page fetch for {url}: status={mock_resp.status_code}, content='{mock_resp.text[:30]}...'")
        return mock_resp
    return side_effect_func

class TestFetchUrlContent(unittest.TestCase):
    def setUp(self):
        # Clear the cache before each test to ensure test isolation
        robot_parsers_cache.clear()

    @patch('aisans.crawler.crawler.requests.get')
    def test_successful_fetch_respects_robots_allow(self, mock_get):
        page_url = "http://example.com/allowedpage.html"
        robots_content = "User-agent: *\nAllow: /"
        page_html_content = "<html><body><h1>Hello World</h1></body></html>"

        mock_get.side_effect = mock_requests_get_side_effect_handler(robots_content, page_html_content)

        with patch('builtins.print'): # Suppress prints from crawler function
            content = fetch_url_content(page_url)

        self.assertEqual(content, page_html_content)
        self.assertEqual(mock_get.call_count, 2)
        # First call for robots.txt
        self.assertEqual(mock_get.call_args_list[0][0][0], "http://example.com/robots.txt")
        self.assertEqual(mock_get.call_args_list[0][1]['headers']['User-Agent'], CRAWLER_USER_AGENT)
        # Second call for the page
        self.assertEqual(mock_get.call_args_list[1][0][0], page_url)
        self.assertEqual(mock_get.call_args_list[1][1]['headers']['User-Agent'], CRAWLER_USER_AGENT)


    @patch('aisans.crawler.crawler.requests.get')
    def test_http_error_for_page_after_robots_allow(self, mock_get):
        page_url = "http://example.com/notfound"
        robots_content = "User-agent: *\nAllow: /"

        mock_get.side_effect = mock_requests_get_side_effect_handler(
            robots_content, "", page_status_code=404
        )

        with patch('builtins.print') as mock_print:
            content = fetch_url_content(page_url)
        
        self.assertIsNone(content)
        mock_print.assert_any_call(f"Failed to fetch {page_url}. Status code: 404")
        self.assertEqual(mock_get.call_count, 2) # robots.txt (OK) + page (404)


    @patch('aisans.crawler.crawler.requests.get')
    def test_request_exception_for_page_after_robots_allow(self, mock_get):
        page_url = "http://example.com/timeout_page"
        robots_content = "User-agent: *\nAllow: /"

        mock_get.side_effect = mock_requests_get_side_effect_handler(
            robots_content, "", page_error=requests.exceptions.Timeout("Page request timed out")
        )

        with patch('builtins.print') as mock_print:
            content = fetch_url_content(page_url)

        self.assertIsNone(content)
        mock_print.assert_any_call(f"Error fetching {page_url}: Page request timed out")
        self.assertEqual(mock_get.call_count, 2) # robots.txt (OK) + page (Exception)

    # New tests for robots.txt specific scenarios
    @patch('aisans.crawler.crawler.requests.get')
    def test_robots_disallows_fetch(self, mock_get):
        robots_content = f"User-agent: {CRAWLER_USER_AGENT}\nDisallow: /private/"
        page_url = "http://example.com/private/page.html"

        mock_get.side_effect = mock_requests_get_side_effect_handler(robots_content, "Page content shouldn't be fetched")

        with patch('builtins.print'):
            content = fetch_url_content(page_url)

        self.assertIsNone(content)
        self.assertEqual(mock_get.call_count, 1) # Only robots.txt should be fetched
        self.assertEqual(mock_get.call_args_list[0][0][0], "http://example.com/robots.txt")

    @patch('aisans.crawler.crawler.requests.get')
    def test_robots_allows_fetch(self, mock_get): # Similar to test_successful_fetch but more explicit
        robots_content = f"User-agent: {CRAWLER_USER_AGENT}\nAllow: /"
        page_url = "http://example.com/allowed/page.html"
        expected_page_content = "Allowed page content"

        mock_get.side_effect = mock_requests_get_side_effect_handler(robots_content, expected_page_content)

        with patch('builtins.print'):
            content = fetch_url_content(page_url)

        self.assertEqual(content, expected_page_content)
        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(mock_get.call_args_list[0][0][0], "http://example.com/robots.txt")
        self.assertEqual(mock_get.call_args_list[1][0][0], page_url)

    @patch('aisans.crawler.crawler.requests.get')
    def test_robots_fetch_fails_allows_page_fetch(self, mock_get):
        page_url = "http://example.com/anotherpage.html"
        expected_page_content = "Content when robots fails"

        # Scenario 1: robots.txt fetch returns 404
        mock_get.side_effect = mock_requests_get_side_effect_handler(
            "", expected_page_content, robots_status_code=404
        )
        with patch('builtins.print'):
            content_404 = fetch_url_content(page_url)
        self.assertEqual(content_404, expected_page_content)
        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(mock_get.call_args_list[0][0][0], "http://example.com/robots.txt")
        self.assertEqual(mock_get.call_args_list[1][0][0], page_url)


        # Scenario 2: robots.txt fetch raises Timeout
        mock_get.reset_mock()
        robot_parsers_cache.clear() # Important: clear cache for this sub-test
        mock_get.side_effect = mock_requests_get_side_effect_handler(
            "", expected_page_content, robots_error=requests.exceptions.Timeout("Robots timeout")
        )
        with patch('builtins.print'):
            content_timeout = fetch_url_content(page_url)
        self.assertEqual(content_timeout, expected_page_content)
        self.assertEqual(mock_get.call_count, 2) # robots.txt (failed with timeout) and page_url
        self.assertEqual(mock_get.call_args_list[0][0][0], "http://example.com/robots.txt")
        self.assertEqual(mock_get.call_args_list[1][0][0], page_url)


    @patch('aisans.crawler.crawler.requests.get')
    def test_robots_parser_caching(self, mock_get):
        robots_content = f"User-agent: {CRAWLER_USER_AGENT}\nDisallow:" # Allow all
        url1 = "http://example.com/page1.html"
        url2 = "http://example.com/page2.html"
        content1 = "Content page 1"
        content2 = "Content page 2"

        # Mock to return robots.txt then page1, then page2
        def detailed_side_effect(url, headers, timeout):
            mock_resp = MagicMock()
            mock_resp.url = url
            if url == "http://example.com/robots.txt":
                # print(f"SIDE_EFFECT: Fetching robots.txt for {url}")
                mock_resp.status_code = 200
                mock_resp.text = robots_content
            elif url == url1:
                # print(f"SIDE_EFFECT: Fetching page {url1}")
                mock_resp.status_code = 200
                mock_resp.text = content1
            elif url == url2:
                # print(f"SIDE_EFFECT: Fetching page {url2}")
                mock_resp.status_code = 200
                mock_resp.text = content2
            else:
                # print(f"SIDE_EFFECT: Unexpected URL {url}")
                mock_resp.status_code = 404
            return mock_resp
        mock_get.side_effect = detailed_side_effect

        with patch('builtins.print'): # Suppress prints from crawler
            res1 = fetch_url_content(url1)
            res2 = fetch_url_content(url2)

        self.assertEqual(res1, content1)
        self.assertEqual(res2, content2)

        self.assertEqual(mock_get.call_count, 3)
        
        robots_fetch_count = 0
        for call_obj in mock_get.call_args_list:
            if "robots.txt" in call_obj[0][0]:
                robots_fetch_count += 1
        self.assertEqual(robots_fetch_count, 1, "robots.txt should only be fetched once due to caching")

if __name__ == '__main__':
    unittest.main()
