import unittest
from unittest.mock import patch, MagicMock
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aisans.metasearch.core import enhance_query_llm, search_all_engines
# LLMClient is imported by aisans.metasearch.core, so we patch it there.

class TestEnhanceQueryLLM(unittest.TestCase):

    @patch('aisans.metasearch.core.LLMClient')
    # Ensure OPENROUTER_API_KEY is set for the duration of this test method for LLMClient to init
    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'fake_key_for_test'})
    def test_enhance_query_llm_success(self, MockLLMClient):
        mock_llm_instance = MockLLMClient.return_value
        mock_llm_instance.generate_text.return_value = "enhanced query"
        original_query = "original query"

        with patch('builtins.print'): # Suppress print statements from enhance_query_llm
            enhanced_query = enhance_query_llm(original_query)

        self.assertEqual(enhanced_query, "enhanced query")
        mock_llm_instance.generate_text.assert_called_once()
        # Optionally check call arguments:
        call_args = mock_llm_instance.generate_text.call_args
        self.assertIn(original_query, call_args.kwargs['prompt'])
        self.assertEqual(call_args.kwargs['model_name'], mock_llm_instance.default_model_name)
        self.assertEqual(call_args.kwargs['max_tokens'], 100)
        self.assertEqual(call_args.kwargs['temperature'], 0.3)

    @patch('aisans.metasearch.core.LLMClient')
    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'fake_key_for_test'})
    def test_enhance_query_llm_returns_none_or_empty(self, MockLLMClient):
        mock_llm_instance = MockLLMClient.return_value
        original_query = "original query"

        # Test case 1: LLM returns None
        mock_llm_instance.generate_text.return_value = None
        with patch('builtins.print'):
            enhanced_query_none = enhance_query_llm(original_query)
        self.assertEqual(enhanced_query_none, original_query)

        # Test case 2: LLM returns empty string (whitespace only)
        mock_llm_instance.generate_text.reset_mock() # Reset call count for next scenario
        mock_llm_instance.generate_text.return_value = "   " # Whitespace only
        with patch('builtins.print'):
            enhanced_query_empty = enhance_query_llm(original_query)
        self.assertEqual(enhanced_query_empty, original_query)

    @patch('aisans.metasearch.core.LLMClient')
    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'fake_key_for_test'})
    def test_enhance_query_llm_returns_same_query(self, MockLLMClient):
        mock_llm_instance = MockLLMClient.return_value
        original_query = "original query"
        mock_llm_instance.generate_text.return_value = "original query" # Same as input

        with patch('builtins.print'):
            enhanced_query = enhance_query_llm(original_query)

        self.assertEqual(enhanced_query, original_query)

    @patch('aisans.metasearch.core.LLMClient')
    @patch.dict(os.environ, {}, clear=True) # Ensure OPENROUTER_API_KEY is NOT set
    def test_enhance_query_llm_no_api_key_env_check(self, MockLLMClient):
        original_query = "original query"

        # The first check `if not os.getenv('OPENROUTER_API_KEY'):` in `enhance_query_llm` should trigger.
        # So, MockLLMClient should not be called.
        with patch('builtins.print'):
            enhanced_query = enhance_query_llm(original_query)

        self.assertEqual(enhanced_query, original_query)
        MockLLMClient.assert_not_called()

    @patch('aisans.metasearch.core.LLMClient')
    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'fake_key_for_init_failure'}) # Key is present for os.getenv
    def test_enhance_query_llm_client_init_raises_value_error(self, MockLLMClient):
        # LLMClient instantiation (the mocked one) should raise ValueError.
        MockLLMClient.side_effect = ValueError("Invalid API key from LLMClient")
        original_query = "original query"

        with patch('builtins.print'):
            enhanced_query = enhance_query_llm(original_query)

        self.assertEqual(enhanced_query, original_query)
        MockLLMClient.assert_called_once() # LLMClient was attempted to be instantiated

    @patch('aisans.metasearch.core.LLMClient')
    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'fake_key_for_test'})
    def test_enhance_query_llm_generate_text_exception(self, MockLLMClient):
        mock_llm_instance = MockLLMClient.return_value
        mock_llm_instance.generate_text.side_effect = Exception("Unexpected API error")
        original_query = "original query"

        with patch('builtins.print'):
            enhanced_query = enhance_query_llm(original_query)

        self.assertEqual(enhanced_query, original_query)
        mock_llm_instance.generate_text.assert_called_once()


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
