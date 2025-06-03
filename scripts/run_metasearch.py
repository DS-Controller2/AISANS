import sys
import os

# Add project root to sys.path to allow imports from the aisans package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aisans.metasearch.core import search_all_engines

def main():
    """
    Main function to run the meta-search test script.
    Prompts the user for a query and displays aggregated search results.
    """
    user_query = input("Enter your search query: ")

    if not user_query.strip():
        print("Query cannot be empty. Exiting.")
        return

    print(f"\nSearching for: '{user_query}' (requesting up to 5 results per engine)...")

    # Call the meta-search function
    # It will internally call the enhance_query_llm placeholder
    results = search_all_engines(query=user_query, max_results_per_engine=5)

    if results:
        print(f"\n--- Found {len(results)} unique results for '{user_query}' (after LLM enhancement) ---")
        for i, result in enumerate(results):
            print(f"\nResult {i+1}:")
            print(f"  Title: {result.get('title', 'N/A')}")
            print(f"  URL: {result.get('url', 'N/A')}")
            print(f"  Snippet: {result.get('snippet', 'N/A')}")
            print(f"  Source: {result.get('source_engine', 'N/A')}")
            print("-" * 20)
    else:
        print(f"\nNo results found for '{user_query}' (after LLM enhancement).")

if __name__ == "__main__":
    main()
