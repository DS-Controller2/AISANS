import unittest
import os
import sqlite3
import shutil # For cleaning up test directories if needed

# Add project root to sys.path to allow imports from aisans package
import sys
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from aisans.indexer.indexer import Indexer

class TestIndexer(unittest.TestCase):
    DB_FILE = os.path.join(os.path.dirname(__file__), 'test_indexer.db') # Store test db in the same dir as test file

    def setUp(self):
        db_dir = os.path.dirname(self.DB_FILE)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        if os.path.exists(self.DB_FILE):
            os.remove(self.DB_FILE)

        self.indexer = Indexer(db_path=self.DB_FILE)
        self.assertIsNotNone(self.indexer.conn, "Failed to initialize Indexer connection.")

        self.doc1 = {
            'url': 'http://example.com/page1', 'title': 'Test Page 1',
            'body': 'This is the first test page about apples.',
            'snippet': 'First test page with apples.', 'source_engine': 'crawler',
            'crawled_timestamp': '2024-01-01T10:00:00Z', 'llm_summary': 'Apples are great fruit.' # Added llm_summary
        }
        self.doc2 = {
            'url': 'http://example.com/page2', 'title': 'Another Test Page 2',
            'body': 'A second page talking about bananas and oranges.',
            'snippet': 'Second page with bananas.', 'source_engine': 'crawler',
            'crawled_timestamp': '2024-01-01T11:00:00Z', 'llm_summary': None # llm_summary can be None
        }
        self.doc3_update_page1 = {
            'url': 'http://example.com/page1', 'title': 'Test Page 1 Updated',
            'body': 'This is the UPDATED first test page about apples and cherries.',
            'snippet': 'UPDATED First test page with apples and cherries.', 'source_engine': 'crawler_v2',
            'crawled_timestamp': '2024-01-01T12:00:00Z', 'llm_summary': 'Apples and cherries are tasty fruits.' # Updated llm_summary
        }

    def tearDown(self):
        if self.indexer:
            self.indexer.close()
        if os.path.exists(self.DB_FILE):
            os.remove(self.DB_FILE)

    def test_create_table_includes_llm_summary(self):
        self.assertIsNotNone(self.indexer.conn, "Database connection should not be None after setUp.")
        cursor = self.indexer.conn.cursor()
        cursor.execute("PRAGMA table_info(pages);")
        columns = [row[1] for row in cursor.fetchall()]
        self.assertIn("llm_summary", columns, "llm_summary column should exist in the pages table.")

    def test_add_single_document_and_retrieve_with_llm_summary(self):
        self.assertTrue(self.indexer.add_document(self.doc1))

        cur = self.indexer.conn.cursor()
        # Use row factory for easier column access by name
        self.indexer.conn.row_factory = sqlite3.Row
        cur = self.indexer.conn.cursor()
        cur.execute("SELECT url, title, body, snippet, llm_summary, source_engine, crawled_timestamp FROM pages WHERE url = ?", (self.doc1['url'],))
        res = cur.fetchone()
        self.assertIsNotNone(res)
        self.assertEqual(res['title'], self.doc1['title'])
        self.assertEqual(res['llm_summary'], self.doc1['llm_summary'])
        self.assertEqual(res['url'], self.doc1['url'])
        self.indexer.conn.row_factory = None # Reset row factory


    def test_add_document_updates_existing_including_llm_summary(self):
        self.indexer.add_document(self.doc1)
        self.assertTrue(self.indexer.add_document(self.doc3_update_page1))

        self.indexer.conn.row_factory = sqlite3.Row
        cur = self.indexer.conn.cursor()
        cur.execute("SELECT title, source_engine, llm_summary FROM pages WHERE url = ?", (self.doc1['url'],))
        res_updated = cur.fetchone()
        self.assertIsNotNone(res_updated)
        self.assertEqual(res_updated['title'], self.doc3_update_page1['title'])
        self.assertEqual(res_updated['source_engine'], self.doc3_update_page1['source_engine'])
        self.assertEqual(res_updated['llm_summary'], self.doc3_update_page1['llm_summary'])

        cur.execute("SELECT COUNT(*) FROM pages")
        count = cur.fetchone()[0]
        self.assertEqual(count, 1, "Update should not create a new row.")
        self.indexer.conn.row_factory = None


    def test_add_document_with_none_llm_summary(self):
        self.assertTrue(self.indexer.add_document(self.doc2))
        self.indexer.conn.row_factory = sqlite3.Row
        cur = self.indexer.conn.cursor()
        cur.execute("SELECT llm_summary FROM pages WHERE url = ?", (self.doc2['url'],))
        res = cur.fetchone()
        self.assertIsNotNone(res)
        self.assertIsNone(res['llm_summary'])
        self.indexer.conn.row_factory = None

    def test_add_batch_documents_with_llm_summary(self):
        doc4 = {
            'url': 'http://example.com/page4', 'title': 'Batch Page 4',
            'body': 'Content for batch page four about dates.',
            'snippet': 'Batch page four.', 'source_engine': 'batch_crawl',
            'crawled_timestamp': '2024-01-02T00:00:00Z', 'llm_summary': 'Dates are sweet.'
        }
        doc5_update_page2 = { # Updates self.doc2
            'url': 'http://example.com/page2', 'title': 'Page 2 Batch Update',
            'body': 'Updated second page via batch, talking about figs.',
            'snippet': 'Page 2 batch update.', 'source_engine': 'batch_crawl_v2',
            'crawled_timestamp': '2024-01-02T01:00:00Z', 'llm_summary': 'Figs are interesting.'
        }

        self.indexer.add_document(self.doc1) # Pre-existing doc
        self.indexer.add_document(self.doc2) # Pre-existing doc that will be updated

        num_added = self.indexer.add_batch([doc4, doc5_update_page2])
        self.assertEqual(num_added, 2)

        self.indexer.conn.row_factory = sqlite3.Row
        cur = self.indexer.conn.cursor()

        res_doc4 = cur.execute("SELECT * FROM pages WHERE url = ?", (doc4['url'],)).fetchone()
        self.assertIsNotNone(res_doc4)
        self.assertEqual(res_doc4['llm_summary'], doc4['llm_summary'])

        res_doc5_updated = cur.execute("SELECT * FROM pages WHERE url = ?", (doc5_update_page2['url'],)).fetchone()
        self.assertIsNotNone(res_doc5_updated)
        self.assertEqual(res_doc5_updated['title'], doc5_update_page2['title'])
        self.assertEqual(res_doc5_updated['llm_summary'], doc5_update_page2['llm_summary'])

        cur.execute("SELECT COUNT(*) FROM pages")
        self.assertEqual(cur.fetchone()[0], 3) # doc1, doc2 (updated), doc4
        self.indexer.conn.row_factory = None

    def test_search_includes_llm_summary_field_and_content(self):
        self.indexer.add_document(self.doc1) # llm_summary: 'Apples are great fruit.'
        self.indexer.add_document(self.doc3_update_page1) # Overwrites doc1, llm_summary: 'Apples and cherries are tasty fruits.'
        self.indexer.add_document(self.doc2) # llm_summary: None

        # Search for term in body
        results_apples = self.indexer.search("cherries")
        self.assertEqual(len(results_apples), 1)
        self.assertEqual(results_apples[0]['url'], self.doc3_update_page1['url'])
        self.assertEqual(results_apples[0]['llm_summary'], self.doc3_update_page1['llm_summary'])

        # Search for term in llm_summary
        results_tasty = self.indexer.search("tasty")
        self.assertEqual(len(results_tasty), 1)
        self.assertEqual(results_tasty[0]['url'], self.doc3_update_page1['url'])
        self.assertEqual(results_tasty[0]['llm_summary'], self.doc3_update_page1['llm_summary'])

        # Search for term that matches a document where llm_summary is None
        results_oranges = self.indexer.search("oranges") # from body of doc2
        self.assertEqual(len(results_oranges), 1)
        self.assertEqual(results_oranges[0]['url'], self.doc2['url'])
        self.assertIsNone(results_oranges[0]['llm_summary'])

        # Ensure all results from a broader query include the llm_summary field
        self.indexer.add_document({
            'url': 'http://example.com/page_generic', 'title': 'Generic Page Content',
            'body': 'Some generic content for testing search.',
            'snippet': 'Generic.', 'source_engine': 'test',
            'crawled_timestamp': '2024-01-04T00:00:00Z', 'llm_summary': 'Generic summary.'
        })
        all_results = self.indexer.search("page") # Should match multiple
        for res in all_results:
            self.assertIn('llm_summary', res.keys())

    def test_add_document_missing_required_fields_handled(self):
        # llm_summary is optional, but other fields are required by the method
        incomplete_doc = {'url': 'http://example.com/incomplete', 'title': 'Incomplete Title'}
        with patch('builtins.print'): # Suppress expected "Document data is missing..." print
            self.assertFalse(self.indexer.add_document(incomplete_doc))

if __name__ == '__main__':
    unittest.main(verbosity=2)
