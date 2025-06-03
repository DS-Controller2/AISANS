import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import os
import shutil
from collections import deque
import logging

# Add project root to sys.path to allow imports from aisans package
import sys
# Assuming the test script is in tests/scripts/
# Go up two levels to reach the project root (where aisans and scripts packages are)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Now import the script and its components
from scripts import run_intelligent_crawler
# Also import specific items that might be directly used or mocked from the script if they are not top-level
from scripts.run_intelligent_crawler import DEFAULT_CONFIG, CONFIG_FILE_PATH, load_config


# Suppress logging output during tests unless specifically testing for it
logging.disable(logging.CRITICAL)

class TestCrawlerConfigLoading(unittest.TestCase):
    def setUp(self):
        # Ensure each test starts with a fresh reference to the original DEFAULT_CONFIG
        self.default_config_copy = DEFAULT_CONFIG.copy()

    @patch('scripts.run_intelligent_crawler.logging') # Mock logging within the module
    @patch('builtins.open', new_callable=mock_open)
    def test_load_config_file_not_found(self, mock_file_open, mock_logging):
        mock_file_open.side_effect = FileNotFoundError
        config = load_config()
        self.assertEqual(config, self.default_config_copy)
        mock_logging.warning.assert_called_with(f"Configuration file {CONFIG_FILE_PATH} not found. Using default settings.")

    @patch('scripts.run_intelligent_crawler.logging')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_config_malformed_json(self, mock_file_open, mock_logging):
        mock_file_open.return_value.read.return_value = "{'bad_json': True,}" # Malformed JSON
        config = load_config()
        self.assertEqual(config, self.default_config_copy)
        mock_logging.warning.assert_called_with(f"Error decoding {CONFIG_FILE_PATH}. Using default settings.")

    @patch('scripts.run_intelligent_crawler.logging')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_config_valid_json_full_override(self, mock_file_open, mock_logging):
        user_settings = {
            "MAX_DEPTH": 5,
            "MAX_PAGES": 200,
            "ENABLE_LLM_SUMMARIZATION": False,
            "SEED_FILE_PATH": "custom/seeds.txt"
        }
        mock_file_open.return_value.read.return_value = json.dumps(user_settings)

        expected_config = self.default_config_copy.copy()
        expected_config.update(user_settings)

        config = load_config()
        self.assertEqual(config, expected_config)
        mock_logging.info.assert_called_with(f"Loaded configuration from {CONFIG_FILE_PATH}")

    @patch('scripts.run_intelligent_crawler.logging')
    @patch('builtins.open', new_callable=mock_open)
    def test_load_config_valid_json_partial_override(self, mock_file_open, mock_logging):
        user_settings = {
            "MAX_DEPTH": 10, # Override
            # MAX_PAGES will use default
            "ENABLE_METASEARCH": False # Override
        }
        mock_file_open.return_value.read.return_value = json.dumps(user_settings)

        expected_config = self.default_config_copy.copy()
        expected_config.update(user_settings) # Apply partial override

        config = load_config()
        self.assertEqual(config, expected_config)
        self.assertEqual(config["MAX_PAGES"], self.default_config_copy["MAX_PAGES"]) # Check default is kept
        mock_logging.info.assert_called_with(f"Loaded configuration from {CONFIG_FILE_PATH}")

class TestIntelligentCrawlerMain(unittest.TestCase):

    def setUp(self):
        self.test_dir = "temp_test_crawler_data"
        self.index_dir = os.path.join(self.test_dir, "indexdir")
        self.config_dir = os.path.join(self.test_dir, "config")
        os.makedirs(self.index_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)

        self.dummy_seeds_file = os.path.join(self.config_dir, "seeds.txt")
        with open(self.dummy_seeds_file, 'w') as f:
            f.write("http://example.com/seed1\n")
            f.write("http://example.com/seed2\n")

        self.dummy_config_file_path = os.path.join(self.config_dir, "crawler_config.json")
        self.base_config_data = {
            "MAX_DEPTH": 1,
            "MAX_PAGES": 2,
            "ENABLE_LLM_SUMMARIZATION": True,
            "OPENROUTER_API_KEY_REQUIRED_FOR_LLM": True, # Assume API key is set via env for tests where LLM is on
            "ENABLE_METASEARCH": True,
            "METASEARCH_INTERVAL": 1, # Trigger metasearch after 1 page
            "MAX_METASEARCH_RESULTS_PER_ENGINE": 1,
            "METASEARCH_QUERY_USE_LLM_SUMMARY": True,
            "SEED_FILE_PATH": self.dummy_seeds_file # Point to our dummy seeds
        }
        with open(self.dummy_config_file_path, 'w') as f:
            json.dump(self.base_config_data, f)

        # Patch external dependencies and components
        # Note: Patching items from 'scripts.run_intelligent_crawler' if they are imported there directly
        # or from their original modules if run_intelligent_crawler imports them (e.g., 'aisans.crawler.crawler.fetch_url_content')

        self.patch_fetch = patch('aisans.crawler.crawler.fetch_url_content')
        self.mock_fetch_url_content = self.patch_fetch.start()

        self.patch_parse = patch('aisans.crawler.parser.parse_html_content')
        self.mock_parse_html_content = self.patch_parse.start()

        self.patch_llm_client = patch('aisans.llm.client.LLMClient')
        self.mock_llm_client_constructor = self.patch_llm_client.start()
        self.mock_llm_instance = MagicMock()
        self.mock_llm_client_constructor.return_value = self.mock_llm_instance

        # For Indexer, we might let it run to create temp files or mock it.
        # For simplicity in this example, let's mock its methods.
        # If Indexer is imported as 'from aisans.indexer.indexer import Indexer' in run_intelligent_crawler
        self.patch_indexer = patch('aisans.indexer.indexer.Indexer')
        self.mock_indexer_constructor = self.patch_indexer.start()
        self.mock_indexer_instance = MagicMock()
        self.mock_indexer_constructor.return_value = self.mock_indexer_instance
        # self.mock_indexer_instance.add_document.return_value = True # Simulate successful add

        self.patch_metasearch = patch('aisans.metasearch.core.search_all_engines')
        self.mock_search_all_engines = self.patch_metasearch.start()

        self.patch_logging = patch('scripts.run_intelligent_crawler.logging') # Patch logging in the SCRIPT
        self.mock_logging_module = self.patch_logging.start()

        # Patch os.getenv for OPENROUTER_API_KEY for tests needing LLM
        self.patch_getenv = patch('os.getenv')
        self.mock_os_getenv = self.patch_getenv.start()
        self.mock_os_getenv.side_effect = lambda key, default=None: 'fake_api_key' if key == 'OPENROUTER_API_KEY' else default


        # Override CONFIG_FILE_PATH in the SCRIPT to use our dummy config
        # This requires careful patching of the global variable in the module.
        self.patch_config_path = patch('scripts.run_intelligent_crawler.CONFIG_FILE_PATH', self.dummy_config_file_path)
        self.patch_config_path.start()

        # Patch LOG_FILE path to avoid creating logs in project root during tests
        self.patch_log_file = patch('scripts.run_intelligent_crawler.LOG_FILE', os.path.join(self.test_dir, "test_crawler.log"))
        self.patch_log_file.start()


    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

        self.patch_fetch.stop()
        self.patch_parse.stop()
        self.patch_llm_client.stop()
        self.patch_indexer.stop()
        self.patch_metasearch.stop()
        self.patch_logging.stop()
        self.patch_getenv.stop()
        self.patch_config_path.stop()
        self.patch_log_file.stop()

    def _update_dummy_config(self, new_config_data):
        # Helper to modify the config for specific tests
        # Merges new_config_data with base_config_data to ensure all keys are present
        # then overwrites the dummy config file.
        full_config = self.base_config_data.copy()
        full_config.update(new_config_data)
        with open(self.dummy_config_file_path, 'w') as f:
            json.dump(full_config, f)
        return full_config # Return the config that will be used

    def test_crawl_process_with_llm_and_metasearch(self):
        self._update_dummy_config({
            "MAX_PAGES": 1, # Process only one page (the first seed)
            "MAX_DEPTH": 0, # Don't follow links from the page itself for this test
            "ENABLE_LLM_SUMMARIZATION": True,
            "ENABLE_METASEARCH": True,
            "METASEARCH_INTERVAL": 1, # Trigger after 1 page
        })

        self.mock_fetch_url_content.return_value = "<html><body>Mocked HTML content for seed1</body></html>"
        self.mock_parse_html_content.return_value = ("Title1", "Text content for seed1", ["http://example.com/newlink1"])
        self.mock_llm_instance.generate_text.return_value = "LLM summary for seed1"
        self.mock_search_all_engines.return_value = [{"url": "http://metasearch.com/meta1", "title": "MetaLink1"}]
        self.mock_indexer_instance.add_document.return_value = True

        run_intelligent_crawler.main()

        self.mock_fetch_url_content.assert_any_call("http://example.com/seed1")
        self.mock_parse_html_content.assert_called_once()
        self.mock_llm_client_constructor.assert_called_once() # LLMClient initialized
        self.mock_llm_instance.generate_text.assert_called_once()

        # Check that add_document was called with the LLM summary
        # The actual call is to self.mock_indexer_instance.add_document
        args, kwargs = self.mock_indexer_instance.add_document.call_args
        self.assertIn('llm_summary', args[0])
        self.assertEqual(args[0]['llm_summary'], "LLM summary for seed1")
        self.assertEqual(args[0]['url'], "http://example.com/seed1")

        self.mock_search_all_engines.assert_called_once()
        self.mock_indexer_instance.close.assert_called_once()

        # Check if metasearch URL was added to queue (inspecting urls_to_visit is tricky as it's local to main)
        # We can check logging output for this, if we log enqueued URLs
        # For now, we assume if search_all_engines was called, its results were processed.
        # A more direct way would be to patch 'deque.append' but that's more intrusive.
        # We can check if fetch was called for the metasearch link if MAX_PAGES allowed it (it doesn't in this config)

    def test_llm_disabled(self):
        self._update_dummy_config({
            "ENABLE_LLM_SUMMARIZATION": False,
            "MAX_PAGES": 1,
            "MAX_DEPTH": 0,
            "ENABLE_METASEARCH": False, # Disable metasearch to simplify
        })

        self.mock_fetch_url_content.return_value = "<html><body>Content</body></html>"
        self.mock_parse_html_content.return_value = ("Title", "Text", [])

        run_intelligent_crawler.main()

        self.mock_llm_instance.generate_text.assert_not_called()
        self.mock_llm_client_constructor.assert_not_called() # If ENABLE_LLM_SUMMARIZATION is false, client might not even be constructed
                                                        # Depending on implementation, it might be constructed then not used.
                                                        # The provided code does construct it then checks the flag. Let's refine.
                                                        # The current run_intelligent_crawler.py code initializes LLMClient *before* checking ENABLE_LLM_SUMMARIZATION for summarization itself.
                                                        # It *does* check ENABLE_LLM_SUMMARIZATION for whether to init the client. This is correct.
                                                        # So, if ENABLE_LLM_SUMMARIZATION is false, constructor shouldn't be called.

        args, kwargs = self.mock_indexer_instance.add_document.call_args
        self.assertIn('llm_summary', args[0]) # Field should still be there
        self.assertIsNone(args[0]['llm_summary']) # But its value should be None


    def test_metasearch_disabled(self):
        self._update_dummy_config({
            "ENABLE_METASEARCH": False,
            "MAX_PAGES": 1,
            "MAX_DEPTH": 0,
        })

        self.mock_fetch_url_content.return_value = "<html><body>Content</body></html>"
        self.mock_parse_html_content.return_value = ("Title", "Text", [])

        run_intelligent_crawler.main()

        self.mock_search_all_engines.assert_not_called()

    @patch('scripts.run_intelligent_crawler.sys.exit') # Mock sys.exit to prevent test runner from exiting
    def test_seed_file_not_found(self, mock_sys_exit):
        # Temporarily change SEED_FILE_PATH in config to a non-existent one for this test
        bad_seed_path = os.path.join(self.config_dir, "non_existent_seeds.txt")
        self._update_dummy_config({"SEED_FILE_PATH": bad_seed_path})

        run_intelligent_crawler.main()

        self.mock_logging_module.error.assert_any_call(f"Seed file {bad_seed_path} not found.")
        # The script should return (or sys.exit) if seed file is not found.
        # If it calls return, main finishes. If sys.exit, we mock it.
        # The current script uses 'return'. So mock_sys_exit might not be called.
        # We're mostly interested in the log message.
        # And that other operations like fetch aren't called
        self.mock_fetch_url_content.assert_not_called()


    def test_fetch_error_handling(self):
        self._update_dummy_config({
            "MAX_PAGES": 1,
            "MAX_DEPTH": 0,
            "ENABLE_LLM_SUMMARIZATION": False, # Simplify
            "ENABLE_METASEARCH": False,      # Simplify
        })

        self.mock_fetch_url_content.return_value = None # Simulate fetch failure

        run_intelligent_crawler.main()

        self.mock_fetch_url_content.assert_called_with("http://example.com/seed1")
        self.mock_parse_html_content.assert_not_called() # Should not parse if fetch fails
        self.mock_indexer_instance.add_document.assert_not_called() # Should not add document
        self.mock_logging_module.warning.assert_any_call(f"No content fetched for http://example.com/seed1. Skipping further processing.")


if __name__ == '__main__':
    # Re-enable logging for test output if run directly, or keep disabled
    # logging.disable(logging.NOTSET)
    unittest.main(verbosity=2)
