import time
import os
from dotenv import load_dotenv

from src.Scraper import Scraper
from src.Telegram import Telegram

load_dotenv()

def main():
    scrape_url = "https://www.zonaprop.com.ar/departamentos-alquiler-palermo-belgrano-nunez-barrio-norte-recoleta-almagro-palermo-hollywood-palermo-soho-hasta-2-ambientes-publicado-hace-menos-de-1-dia"
    scraper = Scraper(scrape_url)
    telegram = Telegram(os.environ["botId"])
    notificados = set()
    while True:
        print("Getting deptos...")
        deptos = scraper.scrape_web()
        print("Deptos obtenidos :)")
        for depto in deptos:
            if depto["id"] not in notificados:
                message = telegram.make_message(depto)
                telegram.send_message(os.environ["chatId"], message)
                notificados.add(depto["id"])
                print("Notif enviada:", depto["id"])
        print("A mimir por 15 mins")
        time.sleep(30*60)

if __name__ == "__main__":
    main()