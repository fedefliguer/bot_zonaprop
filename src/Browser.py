import cloudscraper

class Browser():
    def __init__(self) -> None:
        self.browser = cloudscraper.create_scraper()

    def get(self, url):
        code = -1
        while code != 200:
            try:
                self.browser = cloudscraper.create_scraper()
                req = self.browser.get(url)
                code = req.status_code
            except:
                continue
        return req        

    def get_text(self, url):
        return self.get(url).text