# scraper.py
from bs4 import BeautifulSoup
import re
import json
from typing import Any, Dict, List, Union, Optional

class Scraper:
    """
    A class to handle scraping a single Zonaprop listing and checking its details.
    """
    def __init__(self, browser_instance) -> None:
        """Initializes the scraper with a Browser instance."""
        self.browser = browser_instance
        self.avenidas_caba = ["corrientes", "libertador", "santa fe", "cordoba", "rivadavia", "cabildo", "lacroze", "juan b justo", "constitucion", "callao", "entre rios", "general paz"]

    def reduce_html_to_aviso_info(self, html_text: str) -> Optional[Dict[str, Any]]:
        """
        Busca en el HTML un bloque:  const avisoInfo = { ... };
        """
        if not html_text:
            return None

        match = re.search(r"const\s+avisoInfo\s*=\s*(\{[\s\S]*?\});", html_text, re.DOTALL)
        if not match:
            return None

        raw_obj = match.group(1).strip()

        # Limpieza similar a reduce.py
        # 1) Quitar comas finales antes de ] o }
        cleaned = re.sub(r",\s*([\}\]])", r"\1", raw_obj)
        # 2) Quitar comentarios de línea //
        cleaned = re.sub(r"//.*$", "", cleaned, flags=re.MULTILINE)
        # 3) Poner comillas a claves sin comillas (heurística)
        cleaned = re.sub(r'(\w+)\s*:', r'"\1":', cleaned)

        # Quitar el ; final si quedó
        if cleaned.endswith(';'):
            cleaned = cleaned[:-1].rstrip()

        return cleaned
    

    def parse_number_from_text(self, text):
        """
        Analiza un número de una cadena de texto, manejando formatos comunes.
        """
        text = str(text) 
        if not text:
            return 0
        cleaned_text = re.sub(r'[$,.]', '', text.strip())
        number_match = re.search(r'(\d+)', cleaned_text)
        return int(number_match.group(1)) if number_match else 0
    
    def structured_attributes(self, aviso_info_str: str):
        structured = {}
        
        # Patrones para cada atributo.
        patrones = {
            "id": r"'idAviso':\s*['\"](.*?)['\"]",
            "title": r"'postingTitle'\s*:\s*['\"](.*?)['\"]",
            "price": r"'price'\s*:\s*['\"](.*?)['\"]",
            "currency": r"'pricesData':\s*\[.*?\"currency\":\"(.*?)\"",
            "location": r"'location':\s*{.*?['\"]name['\"]\s*:\s*['\"](.*?)['\"].*?}",
            "property_type": r"'realEstateType':\s*{.*?['\"]name['\"]\s*:\s*['\"](.*?)['\"].*?}",
            "bedrooms": r"['\"]label['\"]\s*:\s*['\"]dorm\.['\"].*?['\"]value['\"]\s*:\s*['\"](.*?)['\"]",
            "bathrooms": r"['\"]label['\"]\s*:\s*['\"]baño['\"].*?['\"]value['\"]\s*:\s*['\"](.*?)['\"]",
            "surface_total": r"['\"]label['\"]\s*:\s*['\"]tot\.['\"].*?['\"]value['\"]\s*:\s*['\"](.*?)['\"]",
            "surface_covered": r"['\"]label['\"]\s*:\s*['\"]cub\.['\"].*?['\"]value['\"]\s*:\s*['\"](.*?)['\"]",
            "description": r"'description'\s*:\s*(.*?)(?=\s*['\"]address['\"]\s*:)",
            "address": r"'address':\s*{.*?['\"]name['\"]\s*:\s*['\"](.*?)['\"].*?}",
            "publisher_id": r"'publisherId':\s*['\"](.*?)['\"]",
            "publisher_name": r"'publisher':\s*{.*?['\"]name['\"]\s*:\s*['\"](.*?)['\"].*?}",
            "whatsapp": r"'whatsApp':\s*['\"](.*?)['\"]",
            "general_features": r"'generalFeatures':\s*({.*?}),\s*'location'",
            "main_features": r"'mainFeatures':\s*({.*?}),\s*'realEstateType'",
        }

        for key, pattern in patrones.items():
            match = re.search(pattern, aviso_info_str, re.DOTALL)
            if match:
                value = match.group(1).strip()
                
                if key in ["general_features", "main_features"]:
                    try:
                        # Reemplazar comillas simples por dobles y corregir sintaxis
                        temp_json_str = value.replace("'", '"')
                        temp_json_str = re.sub(r'\"(null|false|true)\"', r'\1', temp_json_str)
                        
                        parsed_json = json.loads(temp_json_str)
                        structured[key] = parsed_json
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON for {key}: {e}")
                        structured[key] = value
                else:
                    structured[key] = value
        
        # Limpieza adicional para la descripción
        if "description" in structured:
            clean_description = re.sub(r'<[^>]+>', '', structured["description"])
            structured["description"] = clean_description.replace("&quot;", '"').strip()

        return json.dumps(structured, indent=2, ensure_ascii=False)