import unittest
from unittest.mock import patch, MagicMock
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aisans.metasearch.engines import search_duckduckgo, search_google
from duckduckgo_search.exceptions import DuckDuckGoSearchException

class TestSearchDuckDuckGo(unittest.TestCase):
    @patch('aisans.metasearch.engines.DDGS')
    def test_search_duckduckgo_success(self, mock_ddgs_class):
        mock_ddgs_instance = MagicMock()
        mock_ddgs_instance.text.return_value = [
            {'title': 'Test Title 1', 'href': 'http://example.com/1', 'body': 'Snippet 1'},
            {'title': 'Test Title 2', 'href': 'http://example.com/2', 'body': 'Snippet 2'},
        ]
        mock_ddgs_class.return_value = mock_ddgs_instance

        results = search_duckduckgo('test query', num_results=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['title'], 'Test Title 1')
        self.assertEqual(results[0]['url'], 'http://example.com/1')
        self.assertEqual(results[0]['snippet'], 'Snippet 1')
        self.assertEqual(results[0]['source_engine'], 'duckduckgo')
        mock_ddgs_instance.text.assert_called_once_with(keywords='test query', max_results=2)

    @patch('aisans.metasearch.engines.DDGS')
    def test_search_duckduckgo_exception(self, mock_ddgs_class):
        mock_ddgs_instance = MagicMock()
        mock_ddgs_instance.text.side_effect = DuckDuckGoSearchException("Test DDG Error")
        mock_ddgs_class.return_value = mock_ddgs_instance

        # Capturing print output to check error message
        with patch('builtins.print') as mock_print:
            results = search_duckduckgo('test query', num_results=2)
            self.assertEqual(results, [])
            # Check if the specific error message was printed
            # This makes the test more robust to how errors are reported
            printed_error = False
            for call_arg in mock_print.call_args_list:
                if "DuckDuckGo search error: Test DDG Error" in call_arg[0][0]:
                    printed_error = True
                    break
            self.assertTrue(printed_error, "Error message for DuckDuckGoSearchException not printed.")


class TestSearchGoogle(unittest.TestCase):
    @patch('builtins.print') # To capture the print output of the placeholder
    def test_search_google_placeholder(self, mock_print):
        results = search_google('test query', 'dummy_api_key', 'dummy_cse_id', 5)
        self.assertEqual(results, [])
        # Check if the specific placeholder message was printed
        expected_message_part = "Placeholder: Google Search for 'test query'"
        printed_correctly = False
        for call_arg in mock_print.call_args_list:
            if expected_message_part in call_arg[0][0]:
                printed_correctly = True
                break
        self.assertTrue(printed_correctly, f"Expected placeholder message containing '{expected_message_part}' not found in print output.")

if __name__ == '__main__':
    unittest.main()
