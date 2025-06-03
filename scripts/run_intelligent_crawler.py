import sys
import os # For environment variable checking
import datetime
from collections import deque
import urllib.parse # Added for urljoin
import json # Import json for config loading
import logging # Import logging module

# Add project root to sys.path to allow imports from aisans package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aisans.crawler.crawler import fetch_url_content
from aisans.crawler.parser import parse_html_content
from aisans.indexer.indexer import Indexer
from aisans.llm.client import LLMClient # Import LLMClient
from aisans.metasearch.core import search_all_engines # Import Metasearch

DEFAULT_CONFIG = {
    "MAX_DEPTH": 3,
    "MAX_PAGES": 100,
    "ENABLE_LLM_SUMMARIZATION": True,
    "OPENROUTER_API_KEY_REQUIRED_FOR_LLM": True,
    "ENABLE_METASEARCH": True,
    "METASEARCH_INTERVAL": 20,
    "MAX_METASEARCH_RESULTS_PER_ENGINE": 2,
    "METASEARCH_QUERY_USE_LLM_SUMMARY": True,
    "SEED_FILE_PATH": "config/seeds.txt"
}
CONFIG_FILE_PATH = "config/crawler_config.json"
LOG_FILE = "crawler.log"

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(module)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, mode='w'), # Overwrite log file each run
            logging.StreamHandler() # To console
        ]
    )

def load_config():
    config = DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE_PATH, 'r') as f:
            user_config = json.load(f)
        config.update(user_config)
        logging.info(f"Loaded configuration from {CONFIG_FILE_PATH}")
    except FileNotFoundError:
        logging.warning(f"Configuration file {CONFIG_FILE_PATH} not found. Using default settings.")
    except json.JSONDecodeError:
        logging.warning(f"Error decoding {CONFIG_FILE_PATH}. Using default settings.")
    return config

def main():
    """
    Main function to read seed URLs, fetch, parse, index, and print content,
    with queue management, depth control, LLM summarization, and Metasearch integration,
    all configured via a JSON file.
    """
    setup_logging() # Setup logging first
    config = load_config()

    indexer = Indexer()  # Initialize Indexer
    urls_to_visit = deque()
    visited_urls = set()
    pages_crawled = 0
    pages_since_last_metasearch = 0 # Initialize metasearch counter

    # Initialize LLMClient based on config
    llm_client = None
    if config["ENABLE_LLM_SUMMARIZATION"]:
        api_key = os.getenv('OPENROUTER_API_KEY')
        if api_key:
            try:
                llm_client = LLMClient()
                logging.info("LLMClient initialized successfully.")
            except Exception as e:
                logging.warning(f"Failed to initialize LLMClient: {e}. Proceeding without LLM features.")
        elif config["OPENROUTER_API_KEY_REQUIRED_FOR_LLM"]:
            logging.warning("OPENROUTER_API_KEY not set, but ENABLE_LLM_SUMMARIZATION is true. LLM features will be disabled.")
        else:
            logging.info("LLM summarization enabled, API key not set but not strictly required by config. Attempting LLMClient initialization if applicable.")
            try:
                llm_client = LLMClient()
                logging.info("LLMClient initialized (potentially for local/keyless models).")
            except Exception as e:
                logging.warning(f"Failed to initialize LLMClient without API key: {e}. LLM features will be disabled.")
    else:
        logging.info("LLM summarization is disabled in the configuration.")


    try:  # Main try block for ensuring indexer cleanup
        seed_urls = []
        try:
            with open(config["SEED_FILE_PATH"], 'r', encoding='utf-8') as f:
                seed_urls = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            logging.error(f"Seed file not found at {config['SEED_FILE_PATH']}")
            return
        except Exception as e:
            logging.exception(f"Error reading seed file {config['SEED_FILE_PATH']}: {e}")
            return

        if not seed_urls:
            logging.info(f"No URLs found in {config['SEED_FILE_PATH']}. Exiting.")
            return

        for seed_url in seed_urls:
            urls_to_visit.append((seed_url, 0))

        logging.info(f"Starting crawl. Max depth: {config['MAX_DEPTH']}, Max pages: {config['MAX_PAGES']}. Initial queue size: {len(urls_to_visit)}")

        while urls_to_visit and pages_crawled < config["MAX_PAGES"]:
            current_url, current_depth = urls_to_visit.popleft()

            if current_url in visited_urls:
                logging.debug(f"Skipping already visited URL: {current_url}")
                continue

            visited_urls.add(current_url)
            pages_crawled += 1

            logging.info(f"Processing URL (depth {current_depth}, {pages_crawled}/{config['MAX_PAGES']}): {current_url}")

            try:
                html_content = fetch_url_content(current_url) # Already logs its own errors
                if not html_content:
                    logging.warning(f"No content fetched for {current_url}. Skipping further processing.")
                    continue

                title, text_content, extracted_links = "", "", []
                try:
                    title, text_content, extracted_links = parse_html_content(html_content, base_url=current_url)
                except Exception as e:
                    logging.error(f"Failed to parse HTML content for {current_url}: {e}")
                    # Optionally, continue to try to index with what might have been parsed or skip
                    continue # Skip this URL if parsing fails critically

                llm_summary = None
                if llm_client and text_content and config["ENABLE_LLM_SUMMARIZATION"]: # Check ENABLE_LLM_SUMMARIZATION again
                    try:
                        prompt = f"Please summarize the following text in 2-3 sentences:\n\n{text_content[:2000]}"
                        llm_summary = llm_client.generate_text(prompt=prompt, max_tokens=150)
                        if llm_summary:
                            logging.info(f"LLM Summary for {current_url}: {llm_summary[:100]}...")
                        else:
                            logging.warning(f"LLM generated no summary for {current_url}.")
                    except Exception as e:
                logging.warning(f"LLM summarization failed for {current_url}: {e}", exc_info=True) # Added exc_info

                snippet = text_content[:200] + '...' if len(text_content) > 200 else text_content
                doc_data = {
                    'url': current_url,
                    'title': title,
                    'body': text_content,
                    'snippet': snippet,
                    'llm_summary': llm_summary,
                    'source_engine': 'crawler',
                    'crawled_timestamp': datetime.datetime.utcnow().isoformat() + 'Z'
                }

                try:
                    if indexer.add_document(doc_data):
                        logging.info(f"Document {current_url} added to index.")
                    else:
                        # Indexer.add_document should ideally log its own specific errors if it returns False.
                        logging.warning(f"Failed to add document {current_url} to index (indexer returned False).")
                except Exception as e:
                    logging.exception(f"Error adding document {current_url} to index: {e}")


                if current_depth < config["MAX_DEPTH"]:
                    logging.debug(f"Found {len(extracted_links)} links on {current_url}. Enqueuing valid links.")
                    for link in extracted_links:
                        absolute_link = urllib.parse.urljoin(current_url, link)
                        if absolute_link not in visited_urls and not any(item[0] == absolute_link for item in urls_to_visit):
                            urls_to_visit.append((absolute_link, current_depth + 1))
                            logging.debug(f"Enqueued: {absolute_link} (depth {current_depth + 1})")
                else:
                    logging.info(f"Reached max depth ({config['MAX_DEPTH']}) for URL: {current_url}. Not adding further links from this page.")
            # Removed 'else' block for html_content as it's handled by 'continue' earlier if html_content is None.
            except Exception as e: # Catch-all for errors within the processing of a single URL
                logging.exception(f"Unhandled error processing URL {current_url}: {e}")

            pages_since_last_metasearch += 1

            # Metasearch for seed expansion
            if config["ENABLE_METASEARCH"] and pages_since_last_metasearch >= config["METASEARCH_INTERVAL"] and pages_crawled > 0:
                logging.info(f"--- Triggering Metasearch (crawled {pages_crawled}, interval {config['METASEARCH_INTERVAL']}) ---")
                pages_since_last_metasearch = 0

                metasearch_query = None
                # Determine query: Use LLM summary if enabled and available, else use title.
                # 'title' and 'llm_summary' are from the current page's processing earlier in the loop.
                if config["METASEARCH_QUERY_USE_LLM_SUMMARY"] and llm_summary:
                    metasearch_query = llm_summary
                    logging.info(f"Using LLM summary of {current_url} for metasearch query.")
                elif title:
                    metasearch_query = title
                    logging.info(f"Using title of {current_url} for metasearch query.")
                elif seed_urls: # Fallback to the first initial seed URL if current page context is not available
                    metasearch_query = seed_urls[0]
                    logging.info(f"Using first seed URL '{seed_urls[0]}' for metasearch query as fallback.")
                else:
                    logging.warning("No suitable query source for metasearch (current page context or seed URLs).")

                if metasearch_query:
                    try:
                        logging.info(f"Running metasearch with query: '{metasearch_query[:100]}...'")
                        meta_results = search_all_engines(query=metasearch_query, max_results_per_engine=config["MAX_METASEARCH_RESULTS_PER_ENGINE"])
                        if meta_results:
                            logging.info(f"Metasearch found {len(meta_results)} results.")
                            new_links_added_count = 0
                            for result in meta_results:
                                new_url = result.get('url')
                                if new_url and new_url not in visited_urls and not any(item[0] == new_url for item in urls_to_visit):
                                    logging.info(f"Adding new URL from metasearch to queue: {new_url} (depth 0)")
                                    urls_to_visit.append((new_url, 0))
                                    new_links_added_count +=1
                            if new_links_added_count > 0:
                                logging.info(f"Added {new_links_added_count} new unique URLs to queue from metasearch.")
                            else:
                                logging.info("Metasearch results did not yield any new unique URLs.")
                        else:
                            logging.info("Metasearch returned no results.")
                    except Exception as e:
                        logging.warning(f"Metasearch execution failed: {e}", exc_info=True)
                else:
                    logging.info("Skipping metasearch as no suitable query was determined.")

            # Removed the print("-" * 50) as logging provides separators/timestamps.

        logging.info(f"Crawling finished. Total pages visited: {pages_crawled}. URLs remaining in queue: {len(urls_to_visit)}")

    except Exception as e: # Catch-all for errors at the main level (e.g., indexer init, config issues not caught by load_config)
        logging.critical(f"A critical error occurred in the main crawler execution: {e}", exc_info=True)
    finally:
        try:
            indexer.close() # indexer.close() should ideally have its own internal logging for errors
            logging.info("Indexer closed successfully.")
        except Exception as e:
            logging.error(f"Error closing indexer: {e}", exc_info=True)

if __name__ == "__main__":
    main()
