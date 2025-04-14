import requests
from bs4 import BeautifulSoup

def extract_text_from_url(url):
    try:
        resp = requests.get(url, timeout=5)
        soup = BeautifulSoup(resp.text, "html.parser")
        for script in soup(["script", "style"]):
            script.decompose()
        return soup.get_text(separator="\n")
    except Exception:
        return ""
