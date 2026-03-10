import cloudscraper
import time
import requests
import random
import os
from urllib.parse import urlencode

class Browser():
    def __init__(self) -> None:
        self.scraper_api_key = os.environ.get("SCRAPER_API_KEY")
        
        if self.scraper_api_key:
            # Si hay API Key, usamos requests simple ya que ScraperAPI maneja el JS/Cookies
            self.session = requests.Session()
            print("🛡️ ScraperAPI detectada. Usando modo proxy residencial.")
        else:
            # Modo normal (local o sin API key)
            self.session = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True
                }
            )
            print("ℹ️ Iniciando navegador en modo estándar (Cloudscraper).")

        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        ]

    def get(self, url, retries=3, delay=5):
        # Limpieza de URL
        if url.endswith('.html.html'):
            url = url.replace('.html.html', '.html')

        for i in range(retries):
            try:
                if self.scraper_api_key:
                    # Construir la URL de ScraperAPI
                    payload = {
                        'api_key': self.scraper_api_key,
                        'url': url,
                        'render': 'false', # Zonaprop no necesita renderizado JS para el HTML base
                        'premium': 'true'   # Usar IPs residenciales para evitar el 403
                    }
                    proxy_url = 'http://api.scraperapi.com/?' + urlencode(payload)
                    req = self.session.get(proxy_url, timeout=60)
                else:
                    # Modo normal con headers rotativos
                    current_ua = random.choice(self.user_agents)
                    self.session.headers.update({'User-Agent': current_ua})
                    req = self.session.get(url, timeout=30)
                
                req.raise_for_status()
                return req
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Error fetching {url} (Intento {i+1}/{retries}): {e}")
                if i < retries - 1:
                    time.sleep(delay)
                else:
                    print(f"❌ Fallo crítico al obtener {url} tras {retries} reintentos.")
                    return None
        return None

    def get_text(self, url):
        response = self.get(url)
        if response:
            return response.text
        return None
