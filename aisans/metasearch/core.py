# This file will contain the main meta-search logic.

from .engines import search_google, search_duckduckgo
from aisans.llm.client import LLMClient
import os # For checking environment variable if needed for API key status messages

def enhance_query_llm(query: str) -> str:
    """
    Enhances a given search query using an LLM.
    If enhancement fails or the API key is not set, it returns the original query.
    """
    try:
        # Check if OPENROUTER_API_KEY is available for a more informative message,
        # though LLMClient will raise ValueError if it's truly missing.
        if not os.getenv('OPENROUTER_API_KEY'):
            print("LLM Enhancement: OPENROUTER_API_KEY not set. Skipping enhancement.")
            return query # Return original query if API key is definitely not set

        llm_client = LLMClient() # Assumes API key is in env var or passed if client is refactored

        # Using the client's default model (which can be set via OPENROUTER_DEFAULT_MODEL
        # or defaults to a free model like "gryphe/mythomist-7b:free")
        # Or, specify a model directly: model_name="gryphe/mythomist-7b:free"
        model_to_use = llm_client.default_model_name

        prompt = (
            f"Rephrase or improve the following search query for better results, "
            f"focusing on clarity and effectiveness. "
            f"Return only the improved query, without any preamble or explanation. "
            f"Original query: "{query}""
        )

        print(f"Attempting LLM query enhancement for: '{query}' using model {model_to_use}...")
        enhanced_query_text = llm_client.generate_text(
            prompt=prompt,
            model_name=model_to_use, # Explicitly pass for clarity, though it's the default
            max_tokens=100, # Limit output length for a query
            temperature=0.3 # Lower temperature for more focused query output
        )

        if enhanced_query_text and enhanced_query_text.strip() and enhanced_query_text.strip().lower() != query.strip().lower() :
            print(f"LLM Enhanced query: '{enhanced_query_text.strip()}'")
            return enhanced_query_text.strip()
        else:
            if not enhanced_query_text or not enhanced_query_text.strip():
                print(f"LLM Enhancement: Received empty response. Using original query.")
            elif enhanced_query_text.strip().lower() == query.strip().lower():
                print(f"LLM Enhancement: Query unchanged by LLM. Using original query.")
            return query # Return original query if enhancement is empty or same as original

    except ValueError as ve: # Catch API key error from LLMClient
        print(f"LLM Enhancement Error (ValueError): {ve}. Using original query.")
        return query
    except Exception as e:
        print(f"LLM Enhancement Error (Exception): {e}. Using original query.")
        return query

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
    print("\n--- Testing LLM Query Enhancement ---")
    # Note: This test will attempt a live LLM call if OPENROUTER_API_KEY is set.
    # If the API key is not set, the function should gracefully return the original query.
    test_query = "what is quantum computing"
    enhanced = enhance_query_llm(test_query)
    print(f"LLM Enhanced Query Test: Original: '{test_query}', Result: '{enhanced}'")

    test_query_2 = "benefits of open source software development"
    enhanced_2 = enhance_query_llm(test_query_2)
    print(f"LLM Enhanced Query Test 2: Original: '{test_query_2}', Result: '{enhanced_2}'")
