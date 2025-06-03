import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import sqlite3
import tempfile
import datetime

# Add project root to sys.path to allow imports from aisans package and scripts
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Now we can import after sys.path modification
from scripts.run_crawler import main as run_crawler_main
# No need to import Indexer explicitly if we only use sqlite3 to check DB

class TestCrawlerIndexerIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_files = []
        self.env_vars_to_restore = {}

    def tearDown(self):
        for temp_file_path in self.temp_files:
            self._remove_if_exists(temp_file_path)

        for var, value in self.env_vars_to_restore.items():
            if value is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = value

    def _remove_if_exists(self, filepath):
        if not filepath: return
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError as e:
                print(f"Warning: Could not remove file {filepath}: {e}")

            common_suffixes = ['-journal', '-wal', '-shm']
            for suffix in common_suffixes:
                try:
                    journal_file = filepath + suffix
                    if os.path.exists(journal_file):
                        os.remove(journal_file)
                except OSError as e:
                    print(f"Warning: Could not remove journal file {journal_file}: {e}")

    def _set_env_var(self, key, value):
        self.env_vars_to_restore.setdefault(key, os.environ.get(key))
        os.environ[key] = value

    def _unset_env_var(self, key):
        self.env_vars_to_restore.setdefault(key, os.environ.get(key))
        os.environ.pop(key, None)

    @patch('requests.get')
    def test_crawler_indexes_data(self, mock_requests_get):
        # a. Mock HTTP requests
        mock_url = "http://testmock.com/page1"
        sample_html = "<html><head><title>Test Title</title></head><body><p>Test body content with keywords.</p><a href='/anotherpage.html'>Link</a></body></html>"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = sample_html
        mock_requests_get.return_value = mock_response

        # b. Create a temporary seed file
        temp_seed_file = tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8', suffix='.txt')
        self.temp_files.append(temp_seed_file.name)
        temp_seed_file.write(mock_url + "\n")
        temp_seed_file.close()

        # c. Set up a temporary database path
        # Create a temporary file, get its name, then delete it so Indexer can create it
        # This ensures the file is in a writable location and gives a unique name
        temp_db_file = tempfile.NamedTemporaryFile(delete=True, suffix='.db')
        test_db_path = temp_db_file.name
        temp_db_file.close() # Close and delete it
        self.temp_files.append(test_db_path) # Add to temp_files for cleanup in tearDown

        self._set_env_var('AISANS_DB_PATH', test_db_path)

        # d. Patch SEED_FILE_PATH in run_crawler
        # This requires that scripts.run_crawler is already imported.
        with patch('scripts.run_crawler.SEED_FILE_PATH', new=temp_seed_file.name):
            # e. Run the crawler's main function
            try:
                run_crawler_main()
            except SystemExit: # Catch if main() calls sys.exit()
                pass
            except Exception as e:
                self.fail(f"run_crawler_main raised an unexpected exception: {e}")


        # f. Verify database content
        conn = None
        try:
            self.assertTrue(os.path.exists(test_db_path), "Database file was not created.")
            conn = sqlite3.connect(test_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT url, title, body, snippet, source_engine, crawled_timestamp FROM pages WHERE url = ?", (mock_url,))
            row = cursor.fetchone()

            self.assertIsNotNone(row, f"No data found in DB for URL {mock_url}")

            db_url, db_title, db_body, db_snippet, db_source_engine, db_timestamp = row

            self.assertEqual(db_url, mock_url)
            self.assertEqual(db_title, "Test Title")
            self.assertIn("Test body content with keywords.", db_body)
            self.assertTrue(db_snippet.startswith("Test body content with keywords."), "Snippet generation error")
            if len("Test body content with keywords.") > 200:
                 self.assertTrue(db_snippet.endswith("..."), "Snippet should end with ... if truncated")
            self.assertEqual(db_source_engine, "crawler")

            # Verify timestamp format (basic check)
            self.assertIsNotNone(db_timestamp)
            try:
                # Example: 2024-03-16T10:49:51.977115Z
                datetime.datetime.fromisoformat(db_timestamp.replace('Z', '+00:00'))
            except ValueError:
                self.fail(f"Timestamp '{db_timestamp}' is not in expected ISO format with Z suffix.")

        finally:
            if conn:
                conn.close()

        # g. Cleanup is handled by tearDown and context managers for patches

if __name__ == '__main__':
    unittest.main()
