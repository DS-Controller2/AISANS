import unittest
from unittest.mock import patch, MagicMock
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aisans.metasearch.core import enhance_query_llm, search_all_engines

class TestEnhanceQueryLLM(unittest.TestCase):
    def test_enhance_query_llm_placeholder(self):
        query = "free stuff"
        # As enhance_query_llm also prints, we might want to patch print if its output is not desired during tests
        with patch('builtins.print'): # Suppress print during this test
            enhanced = enhance_query_llm(query)
        self.assertEqual(enhanced, "free stuff (enhanced for LLM testing)")

class TestSearchAllEngines(unittest.TestCase):
    @patch('aisans.metasearch.core.search_duckduckgo')
    @patch('aisans.metasearch.core.search_google')
    @patch('aisans.metasearch.core.enhance_query_llm') # Also mock enhance_query_llm
    def test_search_all_engines_calls_selected_engines(self, mock_enhance_llm, mock_search_google, mock_search_duckduckgo):
        original_query = "test query"
        enhanced_query_val = "test query (enhanced for LLM testing)"
        mock_enhance_llm.return_value = enhanced_query_val # Ensure enhance_query_llm is predictable

        mock_search_google.return_value = []
        mock_search_duckduckgo.return_value = []

        with patch('builtins.print'): # Suppress print from search_all_engines
            search_all_engines(original_query, engines_to_use=["google"])
        mock_enhance_llm.assert_called_with(original_query) # Called once for the flow
        mock_search_google.assert_called_once_with(enhanced_query_val, api_key="YOUR_GOOGLE_API_KEY_HERE", cse_id="YOUR_CSE_ID_HERE", num_results=10)
        mock_search_duckduckgo.assert_not_called()

        mock_enhance_llm.reset_mock() # Reset for the next call
        mock_search_google.reset_mock()

        with patch('builtins.print'):
            search_all_engines(original_query, engines_to_use=["duckduckgo"])
        mock_enhance_llm.assert_called_with(original_query) # Called again
        mock_search_duckduckgo.assert_called_once_with(enhanced_query_val, num_results=10)
        mock_search_google.assert_not_called()

    @patch('aisans.metasearch.core.search_duckduckgo')
    @patch('aisans.metasearch.core.search_google')
    @patch('aisans.metasearch.core.enhance_query_llm')
    def test_search_all_engines_deduplication(self, mock_enhance_llm, mock_search_google, mock_search_duckduckgo):
        enhanced_query_val = "test query (enhanced for LLM testing)"
        mock_enhance_llm.return_value = enhanced_query_val

        google_results = [{'title': 'G1', 'url': 'http://example.com/1', 'snippet': 'S1', 'source_engine': 'google'}]
        ddg_results = [
            {'title': 'D1', 'url': 'http://example.com/1', 'snippet': 'S_D1', 'source_engine': 'duckduckgo'}, # Duplicate URL
            {'title': 'D2', 'url': 'http://example.com/2', 'snippet': 'S_D2', 'source_engine': 'duckduckgo'}
        ]
        mock_search_google.return_value = google_results
        mock_search_duckduckgo.return_value = ddg_results

        with patch('builtins.print'):
            results = search_all_engines("test query", engines_to_use=["google", "duckduckgo"])

        self.assertEqual(len(results), 2)
        urls = {res['url'] for res in results}
        self.assertIn('http://example.com/1', urls)
        self.assertIn('http://example.com/2', urls)
        # Ensure the first one encountered (Google's in this case if google is processed first) is kept for the duplicate URL
        self.assertTrue(any(r['url'] == 'http://example.com/1' and r['source_engine'] == 'google' for r in results))


    @patch('aisans.metasearch.core.search_duckduckgo')
    @patch('aisans.metasearch.core.search_google')
    @patch('aisans.metasearch.core.enhance_query_llm')
    def test_search_all_engines_empty_results(self, mock_enhance_llm, mock_search_google, mock_search_duckduckgo):
        enhanced_query_val = "test query (enhanced for LLM testing)"
        mock_enhance_llm.return_value = enhanced_query_val
        mock_search_google.return_value = []
        mock_search_duckduckgo.return_value = []

        with patch('builtins.print'):
            results = search_all_engines("test query")
        self.assertEqual(results, [])

    @patch('aisans.metasearch.core.search_duckduckgo')
    @patch('aisans.metasearch.core.search_google')
    @patch('aisans.metasearch.core.enhance_query_llm')
    def test_search_all_engines_uses_enhanced_query(self, mock_enhance_llm, mock_search_google, mock_search_duckduckgo):
        original_query = "original query"
        enhanced_query_val = "original query (enhanced for LLM testing)"
        mock_enhance_llm.return_value = enhanced_query_val

        mock_search_google.return_value = []
        mock_search_duckduckgo.return_value = []

        with patch('builtins.print'):
            search_all_engines(original_query)

        mock_enhance_llm.assert_called_once_with(original_query)
        mock_search_google.assert_called_once_with(enhanced_query_val, api_key="YOUR_GOOGLE_API_KEY_HERE", cse_id="YOUR_CSE_ID_HERE", num_results=10)
        mock_search_duckduckgo.assert_called_once_with(enhanced_query_val, num_results=10)

if __name__ == '__main__':
    unittest.main()
