import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

def extract_text_from_url(url: str, timeout: int = 5) -> str:
    """
    Extracts visible text content from a given URL using BeautifulSoup.

    Parameters:
    - url (str): The URL to fetch and parse.
    - timeout (int): Timeout duration for the request in seconds.

    Returns:
    - str: Cleaned text content from the webpage, or an error message if failed.
    """
    # Validate the URL
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        return f"[Invalid URL format: {url}]"

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for tag in soup(["script", "style"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        cleaned_text = "\n".join(line.strip() for line in text.splitlines() if line.strip())

        return cleaned_text if cleaned_text else f"[No visible content extracted from {url}]"

    except requests.exceptions.Timeout:
        return f"[Request to {url} timed out after {timeout} seconds.]"
    except requests.exceptions.RequestException as e:
        return f"[Failed to retrieve content from {url}: {e}]"
    except Exception as e:
        return f"[Unexpected error while processing {url}: {e}]"
