import cloudscraper
import time
import requests

class Browser():
    def __init__(self) -> None:
        self.browser = cloudscraper.create_scraper()

    def get(self, url, retries=5, delay=2):
        for i in range(retries):
            try:
                req = self.browser.get(url)
                req.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
                return req
            except requests.exceptions.RequestException as e:
                print(f"Error fetching {url}: {e}")
                if i < retries - 1:
                    print(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    print(f"Failed to fetch {url} after {retries} retries.")
                    return None
        return None

    def get_text(self, url):
        response = self.get(url)
        if response:
            return response.text
        return None