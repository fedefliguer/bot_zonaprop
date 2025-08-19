# one_zonaprop_example.py
from src.Scraper import Scraper
from src.Browser import Browser
import json

def main():
    """
    Orquesta: abre URL, reduce HTML (avisoInfo) y extrae atributos.
    """
    url = "https://www.zonaprop.com.ar/propiedades/clasificado/veclapin-venta-depto-4-amb-en-caballito-apto-credito-56961450.html"

    browser = Browser()
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
    json_structured_info = scraper.structured_attributes(aviso_info)
    print(json_structured_info)

if __name__ == "__main__":
    main()
