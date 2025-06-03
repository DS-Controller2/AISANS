import unittest
import os
import sqlite3
import sys
from datetime import datetime
from unittest.mock import patch # Correct import for patch

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aisans.indexer.indexer import Indexer

class TestIndexer(unittest.TestCase):
    def setUp(self):
        self.test_db_path = "test_aisans_index.db"
        # Ensure the directory for the db_path exists
        # For test_db_path = "test_aisans_index.db", dirname will be empty, so no os.makedirs needed here.
        # If it were "data/test_aisans_index.db", then os.makedirs(os.path.dirname(...)) would be useful.
        # os.makedirs(os.path.dirname(os.path.abspath(self.test_db_path)), exist_ok=True) # Not strictly needed for root path

        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        self.indexer = Indexer(db_path=self.test_db_path)

        # Common test documents
        self.doc1 = {
            'url': 'http://example.com/page1', 'title': 'Apples and Oranges',
            'body': 'This page talks about apples and oranges.',
            'snippet': 'Apples, oranges.', 'source_engine': 'crawler',
            'crawled_timestamp': datetime.now().isoformat()
        }
        self.doc2 = {
            'url': 'http://example.com/page2', 'title': 'Bananas and Pears',
            'body': 'Information about bananas and delicious pears.',
            'snippet': 'Bananas, pears.', 'source_engine': 'meta_ddg',
            'crawled_timestamp': datetime.now().isoformat()
        }
        self.doc3_update_doc1 = {
            'url': 'http://example.com/page1', 'title': 'Apples and Cherries',
            'body': 'Updated: This page is now about apples and also cherries.',
            'snippet': 'Apples, cherries (updated).', 'source_engine': 'crawler_v2',
            'crawled_timestamp': datetime.now().isoformat()
        }

    def tearDown(self):
        if self.indexer: # Ensure indexer was successfully initialized
            self.indexer.close()
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_create_table(self):
        self.assertIsNotNone(self.indexer.conn, "Database connection should not be None after setUp.")
        cursor = self.indexer.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND tbl_name='pages';")
        result = cursor.fetchone()
        self.assertIsNotNone(result, "FTS5 table 'pages' was not created.")

        # Check if it's an FTS table by trying an FTS-specific query
        try:
            cursor.execute("SELECT * FROM pages WHERE pages MATCH 'test';")
        except sqlite3.Error as e:
            self.fail(f"Table 'pages' does not seem to be a functioning FTS5 table: {e}")


    def test_add_single_document_success(self):
        self.assertTrue(self.indexer.add_document(self.doc1))
        cursor = self.indexer.conn.cursor()
        # FTS5 tables don't store columns in the same way, query by `rowid` or indexed columns
        # Or retrieve all columns if they are part of the FTS5 table definition (which they are here)
        cursor.execute("SELECT url, title FROM pages WHERE url = ?", (self.doc1['url'],))
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        # sqlite3.Row can be accessed by index or by name (if row_factory was set, which it is in search, but not here directly)
        self.assertEqual(row[0], self.doc1['url'])
        self.assertEqual(row[1], self.doc1['title'])

    def test_add_single_document_update(self):
        self.indexer.add_document(self.doc1)
        self.assertTrue(self.indexer.add_document(self.doc3_update_doc1)) # Same URL

        cursor = self.indexer.conn.cursor()
        cursor.execute("SELECT title, source_engine FROM pages WHERE url = ?", (self.doc1['url'],))
        row = cursor.fetchone()
        self.assertEqual(row[0], self.doc3_update_doc1['title'])
        self.assertEqual(row[1], self.doc3_update_doc1['source_engine'])

        cursor.execute("SELECT COUNT(*) FROM pages WHERE url = ?", (self.doc1['url'],))
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1)

    def test_add_single_document_missing_fields(self):
        incomplete_doc = {'url': 'http://example.com/incomplete', 'title': 'Incomplete'} # Missing other required fields
        # Patch print to suppress error messages during test
        with patch('builtins.print'):
            self.assertFalse(self.indexer.add_document(incomplete_doc))

        cursor = self.indexer.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM pages WHERE url = ?", (incomplete_doc['url'],))
        self.assertEqual(cursor.fetchone()[0], 0)

    def test_add_batch_success_and_updates(self):
        docs_to_add = [self.doc1, self.doc2, self.doc3_update_doc1] # doc3 updates doc1
        added_count = self.indexer.add_batch(docs_to_add)
        self.assertEqual(added_count, len(docs_to_add))

        cursor = self.indexer.conn.cursor()
        cursor.execute("SELECT title FROM pages WHERE url = ?", (self.doc1['url'],))
        self.assertEqual(cursor.fetchone()[0], self.doc3_update_doc1['title'])

        cursor.execute("SELECT title FROM pages WHERE url = ?", (self.doc2['url'],))
        self.assertEqual(cursor.fetchone()[0], self.doc2['title'])

        cursor.execute("SELECT COUNT(*) FROM pages")
        self.assertEqual(cursor.fetchone()[0], 2)

    def test_add_batch_skip_missing_fields(self):
        valid_doc = {'url': 'http://example.com/valid_batch', 'title': 'Valid', 'body': 'b', 'snippet': 's', 'source_engine': 'se', 'crawled_timestamp': datetime.now().isoformat()}
        invalid_doc = {'url': 'http://example.com/invalid_batch', 'title': 'Invalid'} # Missing required fields
        docs = [valid_doc, invalid_doc, self.doc1]

        with patch('builtins.print'): # Suppress print for missing fields
            added_count = self.indexer.add_batch(docs)
        self.assertEqual(added_count, 2)

        cursor = self.indexer.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM pages")
        self.assertEqual(cursor.fetchone()[0], 2)
        cursor.execute("SELECT url FROM pages WHERE url = ?", (valid_doc['url'],))
        self.assertIsNotNone(cursor.fetchone())
        cursor.execute("SELECT url FROM pages WHERE url = ?", (self.doc1['url'],))
        self.assertIsNotNone(cursor.fetchone())
        cursor.execute("SELECT url FROM pages WHERE url = ?", (invalid_doc['url'],))
        self.assertIsNone(cursor.fetchone())


    def test_search_found(self):
        self.indexer.add_document(self.doc1)
        self.indexer.add_document(self.doc2)

        results = self.indexer.search("apples")
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], dict)
        self.assertEqual(results[0]['url'], self.doc1['url'])
        self.assertIn('rank', results[0])

        results_pears = self.indexer.search("pears")
        self.assertEqual(len(results_pears), 1)
        self.assertEqual(results_pears[0]['url'], self.doc2['url'])

        results_body_terms = self.indexer.search("page talks about")
        self.assertEqual(len(results_body_terms), 1)
        self.assertEqual(results_body_terms[0]['url'], self.doc1['url'])


    def test_search_not_found(self):
        self.indexer.add_document(self.doc1)
        results = self.indexer.search("nonexistentterm123xyz")
        self.assertEqual(len(results), 0)

    def test_search_limit(self):
        self.indexer.add_document(self.doc1) # "apples oranges page"
        self.indexer.add_document(self.doc2) # "bananas pears"
        doc_temp = {
            'url': 'http://example.com/page3', 'title': 'Third Page Item',
            'body': 'Yet another page for testing limit.',
            'snippet': 'Page three.', 'source_engine': 'test',
            'crawled_timestamp': datetime.now().isoformat()
        }
        self.indexer.add_document(doc_temp) # "page"

        results = self.indexer.search("page", limit=1)
        self.assertEqual(len(results), 1)

        results_all = self.indexer.search("page", limit=5)
        # doc1, doc_temp contain "page". doc2 does not.
        self.assertEqual(len(results_all), 2)

    def test_search_empty_query(self):
        self.indexer.add_document(self.doc1)
        # FTS5 behavior with empty query string can be "return all" or error depending on SQLite version / compile options.
        # The search method's try-except sqlite3.Error should catch errors if any.
        # If it returns all, then len(results) > 0. If it errors, len(results) == 0.
        # Let's assume our error handling in search() correctly returns [] for errors.
        with patch('builtins.print'): # Suppress "Error searching index..."
            results = self.indexer.search("")
        self.assertEqual(len(results), 0, "Search with empty query should return empty list (due to FTS error or no match).")

    def test_indexer_context_manager(self):
        temp_db_for_with = "test_aisans_index_with.db"
        if os.path.exists(temp_db_for_with):
            os.remove(temp_db_for_with)

        with Indexer(db_path=temp_db_for_with) as idx:
            idx.add_document(self.doc1)
            self.assertIsNotNone(idx.conn, "Connection should be active inside 'with' block.")

        self.assertIsNone(idx.conn, "Connection should be None after exiting 'with' block and close() is called.")

        # Verify data was written and persisted
        conn_check = sqlite3.connect(temp_db_for_with)
        cursor_check = conn_check.cursor()
        cursor_check.execute("SELECT url FROM pages WHERE url = ?", (self.doc1['url'],))
        self.assertIsNotNone(cursor_check.fetchone())
        conn_check.close()

        if os.path.exists(temp_db_for_with):
            os.remove(temp_db_for_with)

if __name__ == '__main__':
    unittest.main()
