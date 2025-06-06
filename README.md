# AISANS

## Project Overview

AISANS is a search engine project. Its key capabilities include:

*   Crawling web pages to gather information.
*   Parsing the content of crawled pages.
*   Potentially, indexing the parsed content for efficient searching.
*   Providing search functionality to query the indexed data.

## Crawler Component

The crawler component is responsible for fetching web content. It starts with a list of seed URLs and recursively crawls new links found on these pages.

Key functions:

*   `fetch_url_content` (in `aisans/crawler/crawler.py`): This function takes a URL as input and fetches the HTML content of the page.
*   `parse_html_content` (in `aisans/crawler/parser.py`): This function takes HTML content as input, extracts the main textual content, and identifies new links to be crawled.

## Meta-Search Module

The AISANS project now includes a meta-search module designed to aggregate results from multiple search engines for a given query. This allows for a broader range of search results.

**Key Features:**
-   **Multi-Engine Support:** Currently integrates with DuckDuckGo (via the `duckduckgo_search` library) and includes a placeholder for Google Custom Search.
-   **LLM Query Enhancement (Placeholder):** Incorporates a basic placeholder for future LLM-based query enhancement. Currently, it appends a test string to the query.
-   **Deduplication:** Removes duplicate results based on URL.

**Structure:**
-   `aisans/metasearch/core.py`: Contains the main orchestration logic (`search_all_engines`) and the LLM enhancement placeholder (`enhance_query_llm`).
-   `aisans/metasearch/engines.py`: Contains functions for interacting with specific search engines (`search_duckduckgo`, placeholder `search_google`).

## Indexer Module

The Indexer module is responsible for storing and indexing the data fetched by the crawler and meta-search components. This allows for efficient full-text searching of the collected web page information.

**Key Features:**
-   **Backend:** Uses SQLite FTS5 (Full-Text Search engine, version 5) for robust and efficient indexing and querying. Data is stored locally in an SQLite database file (default: `aisans_index.db`).
-   **Schema:** Indexes documents with fields such as `url`, `title`, `body` (full text), `snippet`, `source_engine`, and `crawled_timestamp`.
-   **Functionality:** Provides methods to add individual or batch documents to the index and to search the indexed content.
-   **Tokenizer:** Utilizes the `unicode61 remove_diacritics 2` tokenizer for effective multilingual text processing and case/diacritic insensitive searching.

**Structure:**
-   `aisans/indexer/indexer.py`: Contains the `Indexer` class which encapsulates all indexing and searching logic.

## Project Structure

The project is organized into the following main directories:

*   `aisans/`: Contains the core source code for the search engine.
    *   `crawler/`:  Handles fetching and parsing web content.
    *   `metasearch/`: Aggregates results from multiple search engines and includes LLM query enhancement capabilities.
    *   `indexer/`: Manages the storage and full-text indexing of crawled/fetched data using SQLite FTS5.
    *   `llm/`:  Integrates with large language models (placeholder).
    *   `search/`:  Provides search functionalities (placeholder).
    *   `ui/`: Manages the user interface (placeholder).
*   `config/`: Stores configuration files, such as seed URLs.
*   `scripts/`: Contains utility scripts, like `run_crawler.py`.
*   `tests/`: Includes unit and integration tests for the project.

## Usage/Installation

1.  **Clone the Repository:**
    ```bash
    git clone <repository_url>
    cd aisans
    ```
    *(Replace `https://github.com/DS-Controller2/AISANS.git` with the actual URL of the repository)*

2.  **Install Dependencies:**
    The project uses Python and its dependencies are listed in `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```
    This will install libraries such as `requests` and `beautifulsoup4`.

3.  **Configure Seed URLs:**
    Edit the `config/seeds.txt` file and add the initial URLs you want the crawler to start with, one URL per line.

4.  **Run the Crawler:**
    ```bash
    python scripts/run_crawler.py
    ```

### Configuration for Google Search

To enable Google Search results within the meta-search module:
1.  You will need a Google API Key and a Custom Search Engine (CSE) ID.
2.  Currently, these need to be manually inserted into `aisans/metasearch/core.py` where `YOUR_GOOGLE_API_KEY_HERE` and `YOUR_CSE_ID_HERE` are indicated.
    *Future versions may support environment variables for this configuration.*

## Running Project Scripts

### How to Run the Crawler

The `scripts/run_crawler.py` script is the entry point for running the web crawler.

Make sure you have:
1. Installed all dependencies from `requirements.txt`.
2. Configured your starting URLs in `config/seeds.txt`.

Then, you can run the crawler using:
```bash
python scripts/run_crawler.py
```

This script will initialize the crawler, fetch content starting from the seed URLs, parse the HTML, and extract new links to continue crawling (behavior might be further configurable).

### Running the Meta-Search

To test the meta-search functionality, which queries DuckDuckGo (and a placeholder for Google) and applies a placeholder LLM query enhancement:

```bash
python scripts/run_metasearch.py
```
The script will prompt you to enter a search query.

### Searching the Local Index

After data has been added to the index (e.g., by future modifications to the crawler or meta-search scripts to save their findings), you can search the local index using:

```bash
python scripts/search_index.py
```
This script will prompt you to enter search queries and will display matching documents found in the `aisans_index.db` file (or the database specified by the `AISANS_DB_PATH` environment variable).

## Future Enhancements

This project is currently focused on the crawler implementation. Future development and documentation will cover:

*   **Indexer (`aisans/indexer/`):** Developing the component to store and index the crawled data efficiently.
*   **Search (`aisans/search/`):** Implementing search algorithms and a query interface.
*   **LLM Integration (`aisans/llm/`):** Exploring the use of Large Language Models for tasks like query understanding, summarization, or ranking.
*   **User Interface (`aisans/ui/`):** Creating a user-friendly interface for interacting with the search engine.
*   **Scalability and Robustness:** Improving the crawler's ability to handle large-scale crawls, manage errors, and respect `robots.txt`.
*   **Advanced Parsing:** More sophisticated extraction of specific data types or semantic content.
