import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to sys.path to allow imports from aisans package
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aisans.crawler.crawler import fetch_url_content
import requests

class TestFetchUrlContent(unittest.TestCase):

    @patch('aisans.crawler.crawler.requests.get')
    def test_successful_fetch(self, mock_get):
        # Configure the mock response for a successful fetch
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><h1>Hello World</h1></body></html>"
        mock_get.return_value = mock_response

        url = "http://example.com"
        content = fetch_url_content(url)

        self.assertEqual(content, mock_response.text)
        mock_get.assert_called_once_with(url, headers={"User-Agent": "AISANS-Crawler/0.1"}, timeout=10)

    @patch('aisans.crawler.crawler.requests.get')
    def test_http_error_status_code(self, mock_get):
        # Configure the mock response for an HTTP error
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response

        url = "http://example.com/notfound"
        # Suppress print output during this test
        with patch('builtins.print') as mock_print:
            content = fetch_url_content(url)
            self.assertIsNone(content)
            mock_print.assert_called_with(f"Failed to fetch {url}. Status code: 404")
        
        mock_get.assert_called_once_with(url, headers={"User-Agent": "AISANS-Crawler/0.1"}, timeout=10)

    @patch('aisans.crawler.crawler.requests.get')
    def test_request_exception(self, mock_get):
        # Configure the mock to raise a RequestException (e.g., Timeout)
        url = "http://example.com/timeout"
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        # Suppress print output during this test
        with patch('builtins.print') as mock_print:
            content = fetch_url_content(url)
            self.assertIsNone(content)
            mock_print.assert_called_with(f"Error fetching {url}: Request timed out")

        mock_get.assert_called_once_with(url, headers={"User-Agent": "AISANS-Crawler/0.1"}, timeout=10)

    @patch('aisans.crawler.crawler.requests.get')
    def test_another_request_exception(self, mock_get):
        # Configure the mock to raise a generic RequestException
        url = "http://example.com/networkerror"
        mock_get.side_effect = requests.exceptions.RequestException("Some network error")

        with patch('builtins.print') as mock_print:
            content = fetch_url_content(url)
            self.assertIsNone(content)
            mock_print.assert_called_with(f"Error fetching {url}: Some network error")
        
        mock_get.assert_called_once_with(url, headers={"User-Agent": "AISANS-Crawler/0.1"}, timeout=10)

if __name__ == '__main__':
    unittest.main()
