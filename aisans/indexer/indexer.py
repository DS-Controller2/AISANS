import sqlite3
import os

class Indexer:
    def __init__(self, db_path=None):
        db_path_to_use = db_path if db_path is not None else os.getenv('AISANS_DB_PATH', 'aisans_index.db')
        self.db_path = db_path_to_use
        # Ensure the directory for the db_path exists
        # Use os.path.abspath to handle relative paths correctly before dirname
        abs_db_path = os.path.abspath(self.db_path)
        db_dir = os.path.dirname(abs_db_path)
        if db_dir: # Only create if db_dir is not empty (e.g. db is in current dir)
            os.makedirs(db_dir, exist_ok=True)

        self.conn = None
        self._connect() # Initial connection attempt
        if self.conn: # Only create table if connection was successful
            self._create_table()

    def _connect(self):
        if self.conn is not None: # Already connected
            return
        try:
            self.conn = sqlite3.connect(self.db_path)
            # print(f"Successfully connected to database: {self.db_path}")
        except sqlite3.Error as e:
            print(f"Error connecting to database {self.db_path}: {e}")
            self.conn = None # Ensure conn is None on error
            # raise # Optionally re-raise if connection is critical for instantiation

    def _create_table(self):
        if not self.conn:
            # print("Cannot create table, no database connection.")
            # Attempt to reconnect if not connected.
            self._connect()
            if not self.conn: # Still no connection
                print("Failed to reconnect, cannot create table.")
                return

        try:
            cursor = self.conn.cursor()
            # Schema: url, title, body, snippet, source_engine, crawled_timestamp
            # Tokenizer: unicode61 remove_diacritics 2 (removes diacritics for better matching)
            # remove_diacritics 0=off, 1=on (default, some issues), 2=on (better for all latin chars)
            create_table_sql = """
            CREATE VIRTUAL TABLE IF NOT EXISTS pages USING fts5(
                url UNINDEXED, -- URLs are usually not searched for full-text but used as IDs
                title,
                body,
                snippet,
                source_engine,
                crawled_timestamp,
                tokenize = "unicode61 remove_diacritics 2"
            );
            """
            # Add an index on URL for faster lookups if needed, though FTS5 rowid might be sufficient for primary key ops
            # cursor.execute("CREATE INDEX IF NOT EXISTS idx_url ON pages(url);")
            cursor.execute(create_table_sql)
            # Create an index on the 'url' column for faster lookups and deletions.
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pages_url ON pages(url);")
            self.conn.commit()
            # print("FTS5 'pages' table created or already exists.")
        except sqlite3.Error as e:
            print(f"Error creating FTS5 table 'pages': {e}")
            # Not raising here, as connection might still be valid or table exists.

    def add_document(self, doc_data: dict):
        if not self.conn:
            print("Database connection is not available. Attempting to reconnect...")
            self._connect()
            if not self.conn:
                print("Reconnect failed. Cannot add document.")
                return False

        required_fields = ['url', 'title', 'body', 'snippet', 'source_engine', 'crawled_timestamp']
        if not all(field in doc_data for field in required_fields):
            print(f"Document data is missing one or more required fields ({required_fields}): {doc_data.get('url', 'N/A')}")
            return False

        try:
            cursor = self.conn.cursor()
            # Delete-then-insert strategy for URL uniqueness using FTS5 special delete
            # For FTS tables, deleting by a column value like 'url' requires it to be the rowid or using a subquery if url is not rowid.
            # Assuming url is unique and we want to replace, simpler to delete then insert.
            # If 'url' is specifically made the rowid, this is fine. If not, this might be slow.
            # For FTS5, 'rowid' is the true unique identifier.
            # A common pattern is to store the main content in FTS and have a separate metadata table if complex relations or constraints are needed.
            # Given 'url UNINDEXED', we cannot efficiently use 'WHERE url = ?' for delete on large tables without a separate index.
            # For simplicity in this example, we assume 'url' is effectively unique and can be used to manage document updates.
            # A better FTS5 way if 'url' is not rowid:
            # 1. Query rowid for url: SELECT rowid FROM pages WHERE url = ?
            # 2. If exists, DELETE FROM pages WHERE rowid = ?
            # This requires 'url' to be indexed or a full scan. Since it's UNINDEXED, this is not ideal.
            # Alternative: Let FTS5 handle it by just inserting. Duplicates might occur if not managed.
            # The prompt implies an "upsert" behavior.

            # Let's assume we want to ensure URL is unique by manual deletion first.
            # This will be slow if 'url' is not indexed.
            # For the sake of the example, we proceed but note this performance concern.
            cursor.execute("DELETE FROM pages WHERE url = ?", (doc_data['url'],))

            insert_sql = """
            INSERT INTO pages (url, title, body, snippet, source_engine, crawled_timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            cursor.execute(insert_sql, (
                doc_data.get('url'),
                doc_data.get('title'),
                doc_data.get('body'),
                doc_data.get('snippet'),
                doc_data.get('source_engine'),
                doc_data.get('crawled_timestamp')
            ))
            self.conn.commit()
            # print(f"Document added/updated: {doc_data.get('url')}")
            return True
        except sqlite3.Error as e:
            print(f"Error adding document (URL: {doc_data.get('url')}): {e}")
            try:
                self.conn.rollback()
            except sqlite3.Error as re:
                print(f"Error during rollback: {re}")
            return False

    def add_batch(self, documents: list[dict]):
        if not self.conn:
            print("Database connection is not available. Attempting to reconnect...")
            self._connect()
            if not self.conn:
                print("Reconnect failed. Cannot add batch.")
                return 0

        successful_adds = 0
        try:
            cursor = self.conn.cursor()
            cursor.execute("BEGIN TRANSACTION;")

            delete_sql = "DELETE FROM pages WHERE url = ?"
            insert_sql = """
            INSERT INTO pages (url, title, body, snippet, source_engine, crawled_timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """

            for doc in documents:
                required_fields = ['url', 'title', 'body', 'snippet', 'source_engine', 'crawled_timestamp']
                if not all(field in doc for field in required_fields):
                    print(f"Skipping document in batch due to missing fields (URL: {doc.get('url', 'N/A')})")
                    continue

                cursor.execute(delete_sql, (doc['url'],))
                cursor.execute(insert_sql, (
                    doc.get('url'),
                    doc.get('title'),
                    doc.get('body'),
                    doc.get('snippet'),
                    doc.get('source_engine'),
                    doc.get('crawled_timestamp')
                ))
                successful_adds += 1

            self.conn.commit()
            # print(f"Batch add completed. {successful_adds} documents processed for insertion.")
            return successful_adds
        except sqlite3.Error as e:
            print(f"Error adding batch of documents: {e}")
            try:
                self.conn.rollback()
            except sqlite3.Error as re:
                print(f"Error during rollback: {re}")
            return 0

    def search(self, query_string: str, limit: int = 10) -> list[dict]:
        if not self.conn:
            # Attempt to reconnect if called on a closed or failed indexer
            # print("Database connection is not available for search. Attempting to reconnect...")
            self._connect()
            if not self.conn:
                print("Reconnect failed. Cannot perform search.")
                return []

        original_row_factory = None # Define outside try to ensure it's in scope for finally
        try:
            original_row_factory = self.conn.row_factory # Store original
            self.conn.row_factory = sqlite3.Row # Access columns by name

            cursor = self.conn.cursor()

            # Search across all FTS5 indexed columns by default.
            # Selecting rank to see relevance, and other stored columns.
            search_sql = """
            SELECT url, title, snippet, source_engine, crawled_timestamp, rank
            FROM pages
            WHERE pages MATCH ?
            ORDER BY rank -- BM25 relevance score, lower is better (default for FTS5)
            LIMIT ?
            """
            # Using "pages" as the first argument to MATCH is not standard SQL for FTS5.
            # Usually, you specify column names or the table name itself if all columns are indexed and searched by default.
            # FTS5 by default searches all columns unless specific columns are mentioned (e.g., "pages(title, body) MATCH ?").
            # So, "WHERE pages MATCH ?" is correct for FTS5 to search all indexed columns.

            cursor.execute(search_sql, (query_string, limit))
            results = cursor.fetchall()

            results_as_dict = [dict(row) for row in results]

            return results_as_dict
        except sqlite3.Error as e:
            print(f"Error searching index for query '{query_string}': {e}")
            return []
        finally:
            if self.conn and original_row_factory is not None: # Ensure connection and original_row_factory exist
                self.conn.row_factory = original_row_factory # Reset row_factory

    def close(self):
        if self.conn:
            try:
                self.conn.close()
                self.conn = None
                # print("Database connection closed.")
            except sqlite3.Error as e:
                print(f"Error closing database connection: {e}")

    def __enter__(self):
        # self._connect() # Ensure connection when entering context
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

if __name__ == '__main__':
    # Basic test usage
    DB_FILE = 'test_indexer.db'  # Define DB_FILE for test purposes
    # Ensure the test db directory exists if it's nested, e.g., 'data/test_indexer.db'
    db_dir = os.path.dirname(DB_FILE)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)

    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    print(f"Using database file: {os.path.abspath(DB_FILE)}")
    indexer = Indexer(db_path=DB_FILE)

    if not indexer.conn:
        print("Failed to initialize Indexer connection. Exiting tests.")
        exit(1)

    doc1 = {
        'url': 'http://example.com/page1', 'title': 'Test Page 1', 'body': 'This is the first test page about apples.',
        'snippet': 'First test page with apples.', 'source_engine': 'crawler', 'crawled_timestamp': '2024-01-01T10:00:00Z'
    }
    doc2 = {
        'url': 'http://example.com/page2', 'title': 'Another Test Page 2', 'body': 'A second page talking about bananas and oranges.',
        'snippet': 'Second page with bananas.', 'source_engine': 'crawler', 'crawled_timestamp': '2024-01-01T11:00:00Z'
    }
    doc3_update_page1 = {
        'url': 'http://example.com/page1', 'title': 'Test Page 1 Updated', 'body': 'This is the UPDATED first test page about apples and cherries.',
        'snippet': 'UPDATED First test page with apples and cherries.', 'source_engine': 'crawler_v2', 'crawled_timestamp': '2024-01-01T12:00:00Z'
    }

    print("\nAdding doc1...")
    indexer.add_document(doc1)

    print("\nAdding doc2...")
    indexer.add_document(doc2)

    cur = indexer.conn.cursor()
    cur.execute("SELECT title, source_engine FROM pages WHERE url = ?", (doc1['url'],))
    res = cur.fetchone()
    print(f"\nDoc1 content before update: {res}")
    assert res and res[0] == doc1['title'], f"Doc1 title check failed. Got: {res}"

    print("\nAdding doc3 (update for page1)...")
    indexer.add_document(doc3_update_page1)

    cur.execute("SELECT title, source_engine FROM pages WHERE url = ?", (doc1['url'],))
    res_updated = cur.fetchone()
    print(f"\nDoc1 content after update: {res_updated}")
    assert res_updated and res_updated[0] == doc3_update_page1['title'], f"Doc1 updated title check failed. Got: {res_updated}"
    assert res_updated and res_updated[1] == doc3_update_page1['source_engine'], f"Doc1 updated source_engine check failed. Got: {res_updated}"

    print("\nTesting batch add...")
    doc4 = {
        'url': 'http://example.com/page4', 'title': 'Batch Page 4', 'body': 'Content for batch page four about dates.',
        'snippet': 'Batch page four.', 'source_engine': 'batch_crawl', 'crawled_timestamp': '2024-01-02T00:00:00Z'
    }
    doc5_update_page2 = {
        'url': 'http://example.com/page2', 'title': 'Page 2 Batch Update', 'body': 'Updated second page via batch, talking about figs.',
        'snippet': 'Page 2 batch update.', 'source_engine': 'batch_crawl_v2', 'crawled_timestamp': '2024-01-02T01:00:00Z'
    }
    doc6_missing_fields = {
        'url': 'http://example.com/page6', 'title': 'Page 6 Incomplete',
        'snippet': 'Incomplete.', 'source_engine': 'test', 'crawled_timestamp': '2024-01-02T02:00:00Z'
        # Missing 'body'
    }

    num_added = indexer.add_batch([doc4, doc5_update_page2, doc6_missing_fields])
    print(f"Batch add: {num_added} documents successfully processed for insertion.")
    assert num_added == 2, f"Batch add count mismatch. Expected 2, got {num_added}"

    cur.execute("SELECT COUNT(*) FROM pages")
    total_docs = cur.fetchone()[0]
    print(f"Total documents in index: {total_docs}")
    assert total_docs == 3, f"Total documents mismatch. Expected 3, got {total_docs}"

    cur.execute("SELECT title, source_engine FROM pages WHERE url = ?", (doc5_update_page2['url'],))
    res_batch_updated = cur.fetchone()
    print(f"Doc2 content after batch update: {res_batch_updated}")
    assert res_batch_updated and res_batch_updated[0] == doc5_update_page2['title'], f"Doc2 batch updated title check failed. Got {res_batch_updated}"

    # Test searching (basic FTS5 match) - this part was already present, let's use the new search method
    # print("\nTesting basic FTS search for 'apples':")
    # cur.execute("SELECT url, title FROM pages WHERE pages MATCH 'apples'") # Old way
    # search_results_apples_old = cur.fetchall()
    # print(f"Found {len(search_results_apples_old)} results for 'apples': {search_results_apples_old}")
    # assert len(search_results_apples_old) > 0, "Should find documents mentioning 'apples'"
    # assert any(doc[0] == doc1['url'] for doc in search_results_apples_old), "Doc1 should be in 'apples' search results"

    # print("\nTesting basic FTS search for 'figs':")
    # cur.execute("SELECT url, title FROM pages WHERE pages MATCH 'figs'") # Old way
    # search_results_figs_old = cur.fetchall()
    # print(f"Found {len(search_results_figs_old)} results for 'figs': {search_results_figs_old}")
    # assert len(search_results_figs_old) > 0, "Should find documents mentioning 'figs'"
    # assert any(doc[0] == doc5_update_page2['url'] for doc in search_results_figs_old), "Doc2 (updated) should be in 'figs' search results"

    # --- Testing Search Functionality using the new search() method ---
    print("\n--- Testing Search Functionality ---")

    print("\nSearching for 'apples'...")
    search_results_apples = indexer.search("apples")
    print(f"Found {len(search_results_apples)} results for 'apples':")
    for res_idx, res in enumerate(search_results_apples):
        print(f"  Result {res_idx+1}: URL: {res['url']}, Title: {res['title']}, Snippet: {res['snippet']}, Rank: {res.get('rank', 'N/A')}")
    assert len(search_results_apples) > 0, "Search for 'apples' failed to return results."
    # doc3_update_page1 is the one that has 'apples' and 'cherries' and replaced doc1
    assert any(doc3_update_page1['url'] == res['url'] for res in search_results_apples), "Updated Doc1 should be in 'apples' search results"

    # Create a specific doc for 'bananas' test as original doc2 content was replaced
    doc_banana_search = {
        'url': 'http://example.com/banana_search', 'title': 'Banana Search Test',
        'body': 'This page is specifically about bananas for searching.',
        'snippet': 'Bananas search test.', 'source_engine': 'test_search',
        'crawled_timestamp': '2024-01-03T00:00:00Z'
    }
    print("\nAdding a specific document for 'bananas' search test...")
    indexer.add_document(doc_banana_search)

    print("\nSearching for 'bananas'...")
    search_results_bananas = indexer.search("bananas")
    print(f"Found {len(search_results_bananas)} results for 'bananas':")
    for res_idx, res in enumerate(search_results_bananas):
        print(f"  Result {res_idx+1}: URL: {res['url']}, Title: {res['title']}, Snippet: {res['snippet']}, Rank: {res.get('rank', 'N/A')}")
    assert len(search_results_bananas) > 0, "Search for 'bananas' failed."
    assert any(doc_banana_search['url'] == res['url'] for res in search_results_bananas), "Banana search doc not found."


    print("\nSearching for 'figs' (from batch updated page2)...")
    search_results_figs = indexer.search("figs")
    print(f"Found {len(search_results_figs)} results for 'figs':")
    for res_idx, res in enumerate(search_results_figs):
        print(f"  Result {res_idx+1}: URL: {res['url']}, Title: {res['title']}, Snippet: {res['snippet']}, Rank: {res.get('rank', 'N/A')}")
    assert len(search_results_figs) > 0, "Search for 'figs' failed."
    assert any(doc5_update_page2['url'] == res['url'] for res in search_results_figs), "Updated Doc2 (figs) not found."


    print("\nSearching for 'nonexistentterm123xyz'...")
    search_results_none = indexer.search("nonexistentterm123xyz")
    print(f"Found {len(search_results_none)} results for 'nonexistentterm123xyz'.") # No loop if empty
    assert len(search_results_none) == 0, "Search for nonexistent term should yield 0 results."

    print("\nSearching for 'page' (should match multiple documents)...")
    search_results_page = indexer.search("page") # title and body of many docs contain 'page'
    print(f"Found {len(search_results_page)} results for 'page':")
    for res_idx, res in enumerate(search_results_page):
        print(f"  Result {res_idx+1}: URL: {res['url']}, Title: {res['title']}, Snippet: {res['snippet']}, Rank: {res.get('rank', 'N/A')}")
    # Current docs: doc3_update_page1, doc5_update_page2, doc4, doc_banana_search = 4 total
    # All contain "page" in their content or title.
    assert len(search_results_page) == 4, f"Expected 4 results for 'page', got {len(search_results_page)}"

    print("\n--- Search Functionality Test Completed ---")

    indexer.close()
    print("\nIndexer tests completed (including search).")

    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
