import sys
import os

# Add project root to sys.path to allow imports from aisans package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aisans.indexer.indexer import Indexer

# Define the path to the database file.
# For consistency, let's assume it's in the project root or a 'data' subfolder.
# For this script, using a fixed name in the project root is fine.
# Ensure this path is consistent with where the crawler/meta-search would create it.
DEFAULT_DB_PATH = "aisans_index.db"

def main():
    db_path = os.getenv("AISANS_DB_PATH", DEFAULT_DB_PATH)
    # Ensure the path is absolute for clarity, especially if running from different dirs
    db_path_abs = os.path.abspath(db_path)


    if not os.path.exists(db_path_abs):
        print(f"Error: Index database '{db_path_abs}' not found.")
        print("Please run a script (e.g., crawler or meta-search with indexing enabled) to create and populate the index,")
        print("or ensure AISANS_DB_PATH environment variable is set correctly if using a custom path.")
        return

    try:
        # Using the Indexer as a context manager
        with Indexer(db_path=db_path_abs) as indexer:
            if not indexer.conn: # Check if connection was successful within Indexer's init
                print(f"Failed to connect to the database at {db_path_abs}. Please check the file and permissions.")
                return

            print(f"Successfully connected to index: {db_path_abs}")
            print("Enter your search query (or type 'quit' to exit).")

            while True:
                try:
                    user_query = input("Search: ").strip() # Added strip()
                    if not user_query:
                        continue
                    if user_query.lower() == 'quit':
                        break

                    results = indexer.search(query_string=user_query, limit=10)

                    if results:
                        print(f"\n--- Found {len(results)} results for '{user_query}' ---")
                        for i, res in enumerate(results, 1):
                            print(f"\nResult {i}:")
                            print(f"  Title: {res.get('title', 'N/A')}")
                            print(f"  URL: {res.get('url', 'N/A')}")
                            print(f"  Snippet: {res.get('snippet', 'N/A')}")
                            print(f"  Source: {res.get('source_engine', 'N/A')}")
                            print(f"  Timestamp: {res.get('crawled_timestamp', 'N/A')}")
                            print(f"  Rank: {res.get('rank', 'N/A')}") # FTS5 rank
                            print("-" * 20)
                    else:
                        print(f"No results found for '{user_query}'.")
                except KeyboardInterrupt:
                    print("\nExiting search loop...")
                    break # Exit while loop
                except Exception as e:
                    print(f"An error occurred during search input/processing: {e}")
                    # Depending on the error, you might want to break or continue
                    # For a CLI, often best to break on unexpected errors.
                    break

            print("Exited search.")

    except sqlite3.Error as e: # Catch potential errors from Indexer init (e.g., permission issues)
        print(f"A database error occurred: {e}")
        print(f"Please ensure the database file at {db_path_abs} is a valid SQLite database and accessible.")
    except Exception as e: # Catch any other unexpected errors during setup
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
