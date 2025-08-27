import time
import os
from src.Browser import Browser
from src.Scraper import Scraper
from src.Checker import Checker
from src.Database import Database
from src.Telegram import TelegramNotifier
import json

load_dotenv()

def main():

    scrape_url = "https://www.zonaprop.com.ar/casas-departamentos-ph-venta-villa-crespo-villa-del-parque-caballito-la-paternal-villa-general-mitre-villa-urquiza-colegiales-agronomia-3-ambientes-mas-50-m2-cubiertos-publicado-hace-menos-de-1-dia-menos-160000-dolar.html"
    browser = Browser()
    scraper_list = Scraper(browser_instance=browser, scrape_url=scrape_url)
    new_posts = scraper_list.scrape_web()
    db = Database() # Instanciamos la base de datos
    notifier = TelegramNotifier() # Instanciamos el notificador

    for url in new_posts:
        if not db.property_exists(url):
            print(f"\n{'='*50}\nInmueble nuevo detectado. Iniciando la extracción en: {url}\n")
            
            scraper = Scraper(browser)

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
            
            # Guardamos la propiedad en la base de datos ANTES de procesarla con el Checker
            db.add_property(url, json_structured_info)
            print(f"✅ Inmueble guardado en la base de datos.")

            # 2) Evaluar los atributos con el nuevo Checker
            summary = f'Nuevo aviso detectado: {url}'
            checker = Checker(json_structured_info)
            checker.run_all_checks() # Se corre la nueva función principal de chequeos
            summary = summary + '\n' + checker.get_summary()

            # 4) (Opcional) Lógica de notificación si pasa todos los filtros
            if checker.passed_avenue_check() and checker.passed_price_check():
                notifier.send_message(summary)
            else:
                pass # No se notifica si no pasa los filtros
        else:
            print(f"ℹ️ El inmueble en {url} ya fue procesado anteriormente. Omitiendo.")

    db.close() # Cerramos la conexión a la base de datos al final

if __name__ == "__main__":
    main()
