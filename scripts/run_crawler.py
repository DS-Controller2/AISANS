import sys
import os

import datetime

# Add project root to sys.path to allow imports from aisans package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aisans.crawler.crawler import fetch_url_content
from aisans.crawler.parser import parse_html_content
from aisans.indexer.indexer import Indexer

SEED_FILE_PATH = "config/seeds.txt"

def main():
    """
    Main function to read seed URLs, fetch, parse, index, and print content.
    """
    indexer = Indexer() # Initialize Indexer

    try:
        with open(SEED_FILE_PATH, 'r', encoding='utf-8') as f:
            seed_urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: Seed file not found at {SEED_FILE_PATH}")
        return
    except Exception as e:
        print(f"Error reading seed file {SEED_FILE_PATH}: {e}")
        return

    if not seed_urls:
        print(f"No URLs found in {SEED_FILE_PATH}")
        return

    for url in seed_urls:
        print(f"Processing URL: {url}")
        html_content = fetch_url_content(url)

        if html_content:
            # Use the current URL as base_url for resolving relative links
            title, text_content, extracted_links = parse_html_content(html_content, base_url=url)

            # Prepare document for indexing
            snippet = text_content[:200] + '...' if len(text_content) > 200 else text_content
            doc_data = {
                'url': url,
                'title': title,
                'body': text_content,
                'snippet': snippet,
                'source_engine': 'crawler',
                'crawled_timestamp': datetime.datetime.utcnow().isoformat() + 'Z'
            }

            if indexer.add_document(doc_data):
                print(f"Document {url} added to index.")
            else:
                print(f"Failed to add document {url} to index.")

            print(f"--- Extracted Title for {url} ---")
            print(title)

            print(f"--- Extracted Text for {url} ---")
            if len(text_content) > 500:
                print(text_content[:500] + "... (truncated)")
            else:
                print(text_content)

            print(f"\n--- Extracted Links (first 5) for {url} ---")
            if extracted_links:
                for i, link in enumerate(extracted_links[:5]):
                    print(f"{i+1}. {link}")
            else:
                print("No links found.")
            
            print("-" * 50)
            print()  # Blank line for separation

        else:
            print(f"Skipping {url} due to fetch error or no content.")
            print("-" * 50)
            print() # Blank line for separation
    finally:
        indexer.close()
        print("Indexer closed.")

if __name__ == "__main__":
    main()
