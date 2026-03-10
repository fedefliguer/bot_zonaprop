import time
import os
from src.Browser import Browser
from src.Scraper import Scraper
from src.Checker import Checker
from src.Database import Database
from src.Telegram import TelegramNotifier
import json

def main():

    scrape_url = "https://www.zonaprop.com.ar/ph-alquiler-saavedra-villa-urquiza-coghlan-villa-ortuzar-chacarita-colegiales-agronomia-parque-chas-villa-crespo-caballito-almagro-boedo-san-cristobal-la-paternal-villa-general-mitre-belgrano-r-belgrano-desde-1-hasta-2-habitaciones-desde-2-hasta-3-ambientes-menos-1200000-pesos"
    browser = Browser()
    scraper_list = Scraper(browser_instance=browser, scrape_url=scrape_url)
    new_posts = scraper_list.scrape_web()
    db_url = os.environ.get("DATABASE_URL")
    db = Database(db_url) # Instanciamos la base de datos
    
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    notifier = TelegramNotifier(token=telegram_token, chat_id=telegram_chat_id) # Instanciamos el notificador

    for url in new_posts:
        if not db.property_exists(url):
            print(f"\n{'='*50}\nInmueble nuevo detectado (Gringo). Iniciando la extracción en: {url}\n")
            
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
            
            # Guardamos la propiedad en la base de datos
            db.add_property(url, json_structured_info)
            print(f"✅ Inmueble guardado en la base de datos.")

            # En app_gringo no se realizan checks, se notifica directamente con la ficha
            checker = Checker(json_structured_info)
            summary = f"🚀 Nuevo aviso!\n\n"
            summary += f"🔗 URL: {url}\n\n"
            summary += checker.get_property_ficha()

            notifier.send_message(summary)
            print(f"🚀 Notificación enviada a Telegram.")
            
        else:
            print(f"ℹ️ El inmueble en {url} ya fue procesado anteriormente. Omitiendo.")

    db.close() # Cerramos la conexión a la base de datos al final

if __name__ == "__main__":
    main()
