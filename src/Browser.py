import cloudscraper
import time
import requests
import random

class Browser():
    def __init__(self) -> None:
        # Inicializamos cloudscraper con una configuración de navegador real
        self.browser = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        # Lista de User-Agents modernos para rotar
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0'
        ]

    def get(self, url, retries=5, delay=5):
        # Limpieza básica de la URL por si acaso
        if url.endswith('.html.html'):
            url = url.replace('.html.html', '.html')

        for i in range(retries):
            # Rotar User-Agent y headers en cada intento para evitar patrones fijos
            current_ua = random.choice(self.user_agents)
            self.browser.headers.update({
                'User-Agent': current_ua,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            })
            
            try:
                # Agregar un pequeño delay aleatorio extra
                if i > 0:
                    wait_time = random.uniform(delay, delay + 7)
                    print(f"Waiting {wait_time:.2f}s before retry...")
                    time.sleep(wait_time)
                
                # Realizar la petición con un timeout razonable
                req = self.browser.get(url, timeout=30)
                req.raise_for_status() 
                return req
            except requests.exceptions.RequestException as e:
                print(f"Error fetching {url}: {e}")
                if i < retries - 1:
                    print(f"Retrying ({i+1}/{retries})...")
                else:
                    print(f"Failed to fetch {url} after {retries} retries.")
                    return None
        return None

    def get_text(self, url):
        response = self.get(url)
        if response:
            return response.text
        return None
