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

## Project Structure

The project is organized into the following main directories:

*   `aisans/`: Contains the core source code for the search engine.
    *   `crawler/`:  Handles fetching and parsing web content.
    *   `indexer/`: Responsible for indexing the crawled content (placeholder).
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

## How to Run the Crawler

The `scripts/run_crawler.py` script is the entry point for running the web crawler.

Make sure you have:
1. Installed all dependencies from `requirements.txt`.
2. Configured your starting URLs in `config/seeds.txt`.

Then, you can run the crawler using:
```bash
python scripts/run_crawler.py
```

This script will initialize the crawler, fetch content starting from the seed URLs, parse the HTML, and extract new links to continue crawling (behavior might be further configurable).

## Future Enhancements

This project is currently focused on the crawler implementation. Future development and documentation will cover:

*   **Indexer (`aisans/indexer/`):** Developing the component to store and index the crawled data efficiently.
*   **Search (`aisans/search/`):** Implementing search algorithms and a query interface.
*   **LLM Integration (`aisans/llm/`):** Exploring the use of Large Language Models for tasks like query understanding, summarization, or ranking.
*   **User Interface (`aisans/ui/`):** Creating a user-friendly interface for interacting with the search engine.
*   **Scalability and Robustness:** Improving the crawler's ability to handle large-scale crawls, manage errors, and respect `robots.txt`.
*   **Advanced Parsing:** More sophisticated extraction of specific data types or semantic content.
