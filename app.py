import time
import os
from dotenv import load_dotenv
from src.Browser import Browser
from src.Scraper import Scraper
from src.Checker import Checker
import json
import requests

load_dotenv()

def main():

    scrape_url = "https://www.zonaprop.com.ar/casas-departamentos-ph-venta-villa-crespo-villa-del-parque-caballito-la-paternal-villa-general-mitre-villa-urquiza-colegiales-agronomia-3-ambientes-mas-50-m2-cubiertos-publicado-hace-menos-de-1-dia-menos-160000-dolar.html"
    browser = Browser()
    scraper_list = Scraper(browser_instance=browser, scrape_url=scrape_url)
    new_posts = scraper_list.scrape_web()
    
    for url in new_posts:

        scraper = Scraper(browser)

        print(f"\n{'='*50}\nIniciando la extracción en: {url}\n")

        # 1) Obtener HTML y datos estructurados
        html = browser.get_text(url)
        if not html:
            print("❌ No se pudo obtener el HTML de la URL.")
            continue

        aviso_info = scraper.reduce_html_to_aviso_info(html)
        if not aviso_info:
            print("❌ No se pudo encontrar/parsear 'avisoInfo' dentro del HTML.")
            continue
        
        try:
            json_structured_info = json.loads(scraper.structured_attributes(aviso_info))
        except json.JSONDecodeError:
            print("❌ Error al decodificar el JSON estructurado.")
            continue
        
        # 2) Evaluar los atributos con el nuevo Checker
        summary = f'Nuevo aviso detectado: {url}'
        checker = Checker(json_structured_info)
        checker.run_all_checks() # Se corre la nueva función principal de chequeos
        summary = summary + '\n' + checker.get_summary()

        # 4) (Opcional) Lógica de notificación si pasa todos los filtros
        if checker.passed_avenue_check() and checker.passed_price_check():
            TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
            CHAT_ID = os.environ["CHAT_ID"]
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={summary}"
            response = requests.get(url).json()
            print('Enviado')
        else:
            pass

if __name__ == "__main__":
    main()
