from bs4 import BeautifulSoup
from src.Browser import Browser
import re

PAGE_URL_SUFFIX = '-pagina-'
HTML_EXTENSION = '.html'

base_url = "https://www.zonaprop.com.ar"

class Scraper():
    def __init__(self, scrape_url) -> None:
        self.browser = Browser()
        self.scrape_url = scrape_url

    get_price = lambda self,post: post.find("div", {"data-qa":"POSTING_CARD_PRICE"})
    get_expensas = lambda self,post: post.find("div", {"data-qa":"expensas"})
    get_ubicacion = lambda self,post: post.find("div", {"data-qa":"POSTING_CARD_LOCATION"})
    get_titulo = lambda self,post: post.find("h2").a
    get_url = lambda self,post: base_url + post.find("h2").a["href"]
    get_id = lambda self,url: re.findall("-(\d+).html", url)[0]

    def get_q_publicaciones(self,soup):
        h1 = re.findall(r'\d+\.?\d+', soup.find_all('h1')[0].text)
        res = 0
        if len(h1) > 0:
            res = h1[0]
        return int(res)
    
    def extract_data(self, soup):
        container = soup.find("div", {"class":"postings-container"})
        posts = container.findChildren(recursive=False)
        data = []
        for post in posts:
            price = self.get_price(post)
            expensas = self.get_expensas(post)
            ubicacion = self.get_ubicacion(post)
            titulo = self.get_titulo(post)
            url = self.get_url(post)
            _id = self.get_id(url)
            info = {"precio":"", "expensas":"", "ubicacion": "", "titulo": ""}
            if price != None:
                info["precio"] = price.string
            if expensas != None:
                info["expensas"] = expensas.string.replace("Expensas", "")
            if ubicacion != None:
                info["ubicacion"] = ubicacion.string
            if titulo != None:
                info["titulo"] = titulo.string
            info["url"] = url
            info["id"] = _id
            data.append(info)
        return data
    
    def scrape_web(self):
        page_number = 1
        page_url = f'{self.scrape_url}{HTML_EXTENSION}'
        page = self.browser.get_text(page_url)
        soup = BeautifulSoup(page, 'html.parser')
        cantidad = self.get_q_publicaciones(soup)
        data = self.extract_data(soup)
        while len(data) < cantidad:
            page_number += 1
            page_url = f'{self.scrape_url}{PAGE_URL_SUFFIX}{page_number}{HTML_EXTENSION}'
            page = self.browser.get_text(page_url)
            soup = BeautifulSoup(page, 'html.parser')
            data += self.extract_data(soup)
        return data