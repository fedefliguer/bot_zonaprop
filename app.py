import time
import os
from dotenv import load_dotenv

from src.Scraper import Scraper
from src.Telegram import Telegram

load_dotenv()

def main():
    scrape_url = "https://www.zonaprop.com.ar/inmuebles-venta-villa-crespo-publicado-hace-menos-de-1-dia.html"
    scraper = Scraper(scrape_url)
    telegram = Telegram(os.environ["botId"])
    notificados = set()
    print("Getting deptos...")
    deptos = scraper.scrape_web()
    print("Deptos obtenidos :)")
    for depto in deptos:
        if depto["id"] not in notificados:
            message = telegram.make_message(depto)
            print("Mensaje preparado:\n", message) # Print the message
            # telegram.send_message(os.environ["chatId"], message) # Commented out
            notificados.add(depto["id"])
            print("Notif enviada:", depto["id"])
            break # Exit after processing one depto

if __name__ == "__main__":
    main()
