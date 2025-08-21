# one_zonaprop_example.py
from src.Browser import Browser
from src.Scraper import Scraper
from src.Checker import Checker
import json

def main():
    """
    Orquesta: abre URL, reduce HTML (avisoInfo) y extrae atributos.
    """
    
    url = "https://www.zonaprop.com.ar/propiedades/clasificado/veclapin-3-ambientes-107-m-sup2--a-estrenar-entrega-inmediata-56540649.html"

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
if __name__ == "__main__":
    main()