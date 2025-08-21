import time
import os
from dotenv import load_dotenv
from src.Browser import Browser
from src.Scraper import Scraper
from src.Checker import Checker
from src.Telegram import Telegram
import json

load_dotenv()

def main():

    scrape_url = "https://www.zonaprop.com.ar/departamentos-venta-villa-crespo-villa-del-parque-caballito-la-paternal-villa-general-mitre-villa-urquiza-colegiales-agronomia-3-ambientes-mas-60-m2-cubiertos-publicado-hace-menos-de-1-dia-menos-160000-dolar.html"
    browser = Browser()
    scraper_list = Scraper(browser_instance=browser, scrape_url=scrape_url)
    new_posts = scraper_list.scrape_web()
    
    for url in new_posts:

        scraper = Scraper(browser)

        print(f"Iniciando la extracción en: {url}\n")

        # 1) Obtener HTML crudo
        html = browser.get_text(url)
        if not html:
            print("❌ No se pudo obtener el HTML de la URL.")
            return

        # 2) Extraer atributos
        aviso_info = scraper.reduce_html_to_aviso_info(html)
        if not aviso_info:
            print("❌ No se pudo encontrar/parsear 'avisoInfo' dentro del HTML.")
            return
        
        json_structured_info_str = scraper.structured_attributes(aviso_info)
        
        # Convertir el string JSON a un diccionario de Python
        try:
            json_structured_info = json.loads(json_structured_info_str)
        except json.JSONDecodeError:
            print("❌ Error al decodificar el JSON estructurado.")
            return

        # 3) Evaluar los atributos con la nueva clase Checker
        print('Nuevo aviso detectado: ', url)
        checker = Checker(json_structured_info)
        checker.run_checks()
        print(checker.get_results())
        
        # Obtener y mostrar los contadores
        checks_ok, checks_unknown, checks_fail = checker.get_counts()
        print(f"\nResumen de checks: ✅ {checks_ok} | ❓ {checks_unknown} | ❌ {checks_fail}")

        '''
        telegram = Telegram(os.environ["botId"])
        notificados = set()
        for depto in deptos:
            if depto["id"] not in notificados:
                message = telegram.make_message(depto)
                print("Mensaje preparado:\n", message) # Print the message
                # telegram.send_message(os.environ["chatId"], message) # Commented out
                notificados.add(depto["id"])
                print("Notif enviada:", depto["id"])
                break # Exit after processing one depto
        '''
if __name__ == "__main__":
    main()
