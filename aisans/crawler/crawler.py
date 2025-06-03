import requests
import urllib.robotparser
from urllib.parse import urlparse

# Global cache for RobotFileParser instances
robot_parsers_cache = {}
CRAWLER_USER_AGENT = "AISANS-Crawler/0.1" # Define user agent globally

def fetch_url_content(url: str) -> str | None:
    """
    Fetches the content of a given URL, respecting robots.txt.

    Args:
        url: The URL to fetch.

    Returns:
        The text content of the URL if successful and allowed by robots.txt, None otherwise.
    """
    try:
        parsed_url = urlparse(url)
        scheme = parsed_url.scheme
        netloc = parsed_url.netloc
        if not scheme or not netloc:
            print(f"Invalid URL structure: {url}. Cannot determine robots.txt path.")
            return None

        robots_url = f"{scheme}://{netloc}/robots.txt"
        cache_key = netloc # Use netloc (domain) as the cache key

        if cache_key not in robot_parsers_cache:
            print(f"No robots.txt parser in cache for {netloc}. Fetching {robots_url}")
            parser = urllib.robotparser.RobotFileParser()
            parser.set_url(robots_url)
            try:
                # Use a specific timeout for robots.txt, and same headers
                robots_headers = {"User-Agent": CRAWLER_USER_AGENT}
                # Allow more status codes for robots.txt, as 404 means allow all.
                # However, requests.get will raise for 4xx/5xx by default if not handled.
                # For simplicity, we'll rely on status_code check.
                response_robots = requests.get(robots_url, headers=robots_headers, timeout=5)
                if response_robots.status_code == 200:
                    parser.parse(response_robots.text.splitlines())
                    print(f"Successfully fetched and parsed robots.txt for {netloc}")
                elif response_robots.status_code >= 400 and response_robots.status_code < 500:
                     print(f"Client error ({response_robots.status_code}) fetching robots.txt for {netloc}. Assuming allow all.")
                     # Parser remains empty, effectively allowing all.
                else: # Other errors or server issues
                    print(f"Failed to fetch robots.txt for {netloc}. Status: {response_robots.status_code}. Assuming allow all.")
            except requests.exceptions.Timeout:
                print(f"Timeout fetching robots.txt for {netloc}. Assuming allow all.")
            except requests.exceptions.RequestException as e:
                print(f"Error fetching robots.txt for {netloc}: {e}. Assuming allow all.")
            robot_parsers_cache[cache_key] = parser
        else:
            print(f"Found robots.txt parser in cache for {netloc}.")
            parser = robot_parsers_cache[cache_key]

        if not parser.can_fetch(CRAWLER_USER_AGENT, url):
            print(f"Fetching DISALLOWED for {url} by robots.txt on {netloc}")
            return None
        else:
            print(f"Fetching ALLOWED for {url} by robots.txt on {netloc}")

        # Proceed to fetch the actual URL content
        headers = {
            "User-Agent": CRAWLER_USER_AGENT
        }
        response_url = requests.get(url, headers=headers, timeout=10)
        if response_url.status_code == 200:
            return response_url.text
        else:
            print(f"Failed to fetch {url}. Status code: {response_url.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None
    except Exception as e: # Catch any other unexpected errors (e.g., in urlparse)
        print(f"An unexpected error occurred while trying to fetch {url}: {e}")
        return None


if __name__ == '__main__':
    print(f"--- Crawler Test ---")
    print(f"Using User-Agent: {CRAWLER_USER_AGENT}")

    # Example URLs for testing robots.txt
    # Google is generally restrictive, wikipedia more open for well-behaved crawlers
    test_urls = [
        "https://www.google.com/search", # Likely disallowed
        "https://en.wikipedia.org/wiki/Main_Page", # Likely allowed
        "https://www.python.org/", # Likely allowed
        "https://invalid.url.that.does.not.exist/for_robots_test", # Test error handling
        "http://127.0.0.1:9999/nonexistent_robots.txt" # Test connection error for robots.txt
    ]

    for test_url in test_urls:
        print(f"\n--- Testing URL: {test_url} ---")
        content = fetch_url_content(test_url)
        if content:
            print(f"Successfully fetched content from {test_url[:80]}...")
            # print(content[:200] + "..." if len(content) > 200 else content) # Optional: print snippet
        else:
            print(f"Failed to fetch or was disallowed for {test_url}")
        print("-" * 40)

    # Example of cache being used
    print("\n--- Testing robots.txt cache ---")
    print("Fetching a Wikipedia page again (should use cached robots.txt parser):")
    content_wiki_again = fetch_url_content("https://en.wikipedia.org/wiki/Python_(programming_language)")
    if content_wiki_again:
        print(f"Successfully fetched content from Wikipedia again.")
    else:
        print(f"Failed to fetch content from Wikipedia again.")
