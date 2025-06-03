# This file will contain the main meta-search logic.

from .engines import search_google, search_duckduckgo

def enhance_query_llm(query: str) -> str:
    """
    Placeholder function to enhance a query using an LLM.
    Currently, it appends a static string for testing purposes.
    """
    # TODO: Replace this placeholder with actual LLM query enhancement logic.
    # This could involve API calls to an LLM to refine, expand, or rephrase the query.
    enhanced_query = f"{query} (enhanced for LLM testing)"
    print(f"Original query: '{query}', Enhanced query: '{enhanced_query}'")
    return enhanced_query

def search_all_engines(query: str, max_results_per_engine: int = 10, engines_to_use: list[str] = None) -> list[dict]:
    """
    Searches the query across specified search engines and aggregates unique results.

    Args:
        query: The search query string.
        max_results_per_engine: Maximum number of results to fetch from each engine.
        engines_to_use: A list of engine names (e.g., ["google", "duckduckgo"]).
                        Defaults to all implemented engines if None.

    Returns:
        A list of unique search result dictionaries.
    """
    if engines_to_use is None:
        engines_to_use = ["google", "duckduckgo"]

    all_results = []
    seen_urls = set()

    # Enhance the query using the LLM placeholder
    enhanced_query = enhance_query_llm(query)

    print(f"Meta-search for original query: '{query}' (enhanced to: '{enhanced_query}') using engines: {engines_to_use}, max {max_results_per_engine} results per engine.")

    if "google" in engines_to_use:
        print("Querying Google with enhanced query...")
        # Using placeholder API key and CSE ID as per instructions
        google_results = search_google(
            enhanced_query,  # Use enhanced query
            api_key="YOUR_GOOGLE_API_KEY_HERE",
            cse_id="YOUR_CSE_ID_HERE",
            num_results=max_results_per_engine
        )
        for result in google_results:
            if result.get('url') and result['url'] not in seen_urls:
                all_results.append(result)
                seen_urls.add(result['url'])
        print(f"Added {len(google_results)} results from Google (before deduplication).")


    if "duckduckgo" in engines_to_use:
        print("Querying DuckDuckGo with enhanced query...")
        ddg_results = search_duckduckgo(enhanced_query, num_results=max_results_per_engine) # Use enhanced query
        for result in ddg_results:
            if result.get('url') and result['url'] not in seen_urls:
                all_results.append(result)
                seen_urls.add(result['url'])
        print(f"Added {len(ddg_results)} results from DuckDuckGo (before deduplication with Google).")

    print(f"Total unique results after meta-search: {len(all_results)}")
    return all_results

if __name__ == '__main__':
    print("Testing meta-search functionality...")

    # Test with DuckDuckGo only first
    print("\n--- Testing with DuckDuckGo only ---")
    results_ddg_only = search_all_engines("python programming best practices", max_results_per_engine=3, engines_to_use=["duckduckgo"])
    for i, res in enumerate(results_ddg_only):
        print(f"{i+1}. {res['title']} ({res['url']}) - {res['source_engine']}")

    # Test with Google only (will use placeholder)
    print("\n--- Testing with Google only (placeholder) ---")
    results_google_only = search_all_engines("ai advancements", max_results_per_engine=3, engines_to_use=["google"])
    for i, res in enumerate(results_google_only): # Should be empty
        print(f"{i+1}. {res['title']} ({res['url']}) - {res['source_engine']}")
    if not results_google_only:
        print("No results from Google (placeholder), as expected.")

    # Test with both (Google placeholder + DuckDuckGo)
    print("\n--- Testing with both Google (placeholder) and DuckDuckGo ---")
    results_both = search_all_engines("latest technology trends", max_results_per_engine=3) # Default uses both
    for i, res in enumerate(results_both):
        print(f"{i+1}. {res['title']} ({res['url']}) - {res['source_engine']}")

    print("\nMeta-search tests complete.")

    # Test enhance_query_llm
    print("\n--- Testing LLM Query Enhancement (Placeholder) ---")
    test_query = "what is quantum computing"
    enhanced = enhance_query_llm(test_query)
    print(f"LLM Enhanced Query Test: Original: '{test_query}', Result: '{enhanced}'")

    test_query_2 = "benefits of open source"
    enhanced_2 = enhance_query_llm(test_query_2)
    print(f"LLM Enhanced Query Test 2: Original: '{test_query_2}', Result: '{enhanced_2}'")
