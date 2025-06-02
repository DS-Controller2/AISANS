import requests

def fetch_url_content(url: str) -> str | None:
    """
    Fetches the content of a given URL.

    Args:
        url: The URL to fetch.

    Returns:
        The text content of the URL if successful, None otherwise.
    """
    headers = {
        "User-Agent": "AISANS-Crawler/0.1"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to fetch {url}. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

if __name__ == '__main__':
    # Example usage (optional)
    test_url = "https://www.google.com"
    content = fetch_url_content(test_url)
    if content:
        print(f"Successfully fetched content from {test_url[:50]}...")
    else:
        print(f"Failed to fetch content from {test_url}")

    test_url_invalid = "https://invalid.url.that.does.not.exist"
    content_invalid = fetch_url_content(test_url_invalid)
    if content_invalid:
        print(f"Successfully fetched content from {test_url_invalid[:50]}...")
    else:
        print(f"Failed to fetch content from {test_url_invalid}")
