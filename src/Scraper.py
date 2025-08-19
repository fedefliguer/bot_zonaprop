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
        cleaned = re.sub(r",\s*([\]\}])", r"\1", raw_obj)
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
    
    def process_listing(self, url):
        """
        Procesa un único aviso de propiedad de forma síncrona, obteniendo los datos
        de diferentes partes del HTML para mayor robustez.
        """
        try:
            print(f"Obteniendo datos de la URL: {url}")
            html_content = self.browser.get_text(url)
            if not html_content:
                print("El contenido HTML está vacío.")
                return None
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            scraped_data = {
                "bathrooms": 0,
                "toilettes": 0,
                "age": 0,
                "expensas": 0,
                "covered_area": 0,
                "total_area": 0,
                "has_balcony_or_patio": False,
                "has_elevator": False,
                "has_laundry": False,
                "has_gas_kitchen": False,
                "address": "",
                "avenue_name": ""
            }

            # 1. Extraer datos del script JSON-LD (Schema.org)
            scripts = soup.find_all('script', {'type': 'application/ld+json'})
            for script in scripts:
                try:
                    json_data = json.loads(script.string)
                    if isinstance(json_data, dict) and json_data.get('@type') in ['Apartment', 'House']:
                        scraped_data["bathrooms"] = json_data.get('numberOfBathroomsTotal', 0)
                        if 'floorSize' in json_data and json_data['floorSize'].get('unitCode') == 'MTK':
                            scraped_data["covered_area"] = json_data['floorSize'].get('value', 0)
                        if 'address' in json_data and 'streetAddress' in json_data['address']:
                            address_name = json_data['address']['streetAddress'].strip().lower()
                            scraped_data["address"] = address_name
                            # Detección del nombre de la avenida
                            for avenue in self.avenidas_caba:
                                if avenue in address_name:
                                    scraped_data["avenue_name"] = avenue
                                    break
                except json.JSONDecodeError:
                    continue

            # 2. Extraer datos de la sección de características con iconos
            features_section = soup.find("ul", {"id": "section-icon-features-property"})
            if features_section:
                for li in features_section.find_all("li", class_="icon-feature"):
                    text = li.text.lower()
                    if 'baño' in text:
                        toilettes_match = re.search(r'(\d+)\s*toilette', text)
                        if toilettes_match:
                            scraped_data["toilettes"] = self.parse_number_from_text(toilettes_match.group(1))
                        bathrooms_match = re.search(r'(\d+)\s*baño', text)
                        if bathrooms_match:
                            scraped_data["bathrooms"] = self.parse_number_from_text(bathrooms_match.group(1))
                    elif 'años' in text:
                        age_match = re.search(r'(\d+)\s*años', text)
                        if age_match:
                            scraped_data["age"] = self.parse_number_from_text(age_match.group(1))
                    elif 'm² tot' in text:
                        total_area_match = re.search(r'(\d+)\s*m²\s*tot', text)
                        if total_area_match:
                            scraped_data["total_area"] = self.parse_number_from_text(total_area_match.group(1))
                    elif 'm² cub' in text:
                        covered_area_match = re.search(r'(\d+)\s*m²\s*cub', text)
                        if covered_area_match:
                            scraped_data["covered_area"] = self.parse_number_from_text(covered_area_match.group(1))
            
            scraped_data["bathrooms"] += scraped_data["toilettes"]

            # 3. Extraer datos de la descripción y el texto completo
            description_text = soup.find("div", {"class": "section-description"}).text.lower() if soup.find("div", {"class": "section-description"}) else ""
            full_text_lower = soup.text.lower()

            expensas_match = re.search(r'expensas\s*(\$|\d+\s*\$)\s*([\d\.]+)[\.,]?\d*', full_text_lower)
            if expensas_match:
                expensas_str = expensas_match.group(2).replace('.', '').replace(',', '')
                scraped_data["expensas"] = int(expensas_str) if expensas_str.isdigit() else 0

            scraped_data["has_balcony_or_patio"] = "balcón" in description_text or "patio" in description_text
            scraped_data["has_gas_kitchen"] = "cocina a gas" in description_text
            scraped_data["has_elevator"] = "ascensor" in full_text_lower
            scraped_data["has_laundry"] = "lavadero" in full_text_lower

            print("Datos de la propiedad extraídos exitosamente:")
            print(json.dumps(scraped_data, indent=4))
            
            return self.check_requirements(scraped_data)

        except Exception as e:
            print(f"❌ Ocurrió un error durante el scraping: {e}")
            return None

    def check_requirements(self, data):
        """
        Verifica si los datos de la propiedad cumplen con los requisitos deseables
        y devuelve un diccionario con el estado de cada uno.
        """
        criteria = {}
        
        # 1. Tiene dos baños o más (sumando baño y toilette)
        total_bathrooms = data.get("bathrooms", 0)
        criteria["Tiene dos baños o más"] = (total_bathrooms >= 2, f"{total_bathrooms} baño{'s' if total_bathrooms != 1 else ''}")
        
        # 2. Antigüedad menor a 50 años
        age = data.get("age", 0)
        criteria["Antigüedad menor a 50 años"] = (age < 50 and age > 0, f"{age} años")
        
        # 3. Expensas menores a $150.000
        expensas = data.get("expensas", 0)
        criteria["Expensas menores a $150.000"] = (expensas < 150000 and expensas > 0, f"${expensas:,} o no tiene" if expensas > 0 else "No tiene expensas o no se encontraron")
        
        # 4. Más de 60m2 cubiertos
        covered_area = data.get("covered_area", 0)
        criteria["Más de 60m2 cubiertos"] = (covered_area > 60, f"{covered_area}m² cubiertos")
        
        # 5. Balcón, patio, o más m2 totales que cubiertos
        has_balcony_or_patio = data.get("has_balcony_or_patio", False)
        total_area = data.get("total_area", 0)
        has_extra_space = total_area > covered_area
        
        status_extra_space = has_balcony_or_patio or has_extra_space
        reason_extra_space = ""
        if not status_extra_space:
            reason_extra_space = f"No se encontró balcón ni patio y los m² totales ({total_area}) no son mayores que los cubiertos ({covered_area})"
        elif has_balcony_or_patio and not has_extra_space:
            reason_extra_space = "Se encontró balcón/patio, pero no hay más m² totales que cubiertos"
        elif not has_balcony_or_patio and has_extra_space:
            reason_extra_space = f"Hay más m² totales ({total_area}) que cubiertos ({covered_area})"
        else:
            reason_extra_space = "Se encontró balcón/patio y hay más m² totales que cubiertos"
        criteria["Balcón, patio, o más m2 totales que cubiertos"] = (status_extra_space, reason_extra_space)

        # 6. Tiene ascensor
        has_elevator = data.get("has_elevator", False)
        criteria["Tiene ascensor"] = (has_elevator, "No se encontró la palabra 'ascensor'" if not has_elevator else "Sí, se encontró")
        
        # 7. Tiene lavadero
        has_laundry = data.get("has_laundry", False)
        criteria["Tiene lavadero"] = (has_laundry, "No se encontró la palabra 'lavadero'" if not has_laundry else "Sí, se encontró")
        
        # 8. Tiene cocina a gas
        has_gas_kitchen = data.get("has_gas_kitchen", False)
        criteria["Tiene cocina a gas"] = (has_gas_kitchen, "No se encontró la frase 'cocina a gas' en la descripción" if not has_gas_kitchen else "")

        # 9. No está en una avenida
        address = data.get("address", "")
        is_on_avenue = bool(data.get("avenue_name"))
        not_on_avenue = not is_on_avenue
        reason_avenue = None
        if is_on_avenue:
            reason_avenue = f"La dirección está sobre la avenida {data.get('avenue_name').title()}."
        criteria["No está en una avenida"] = (not_on_avenue, reason_avenue)
        
        return criteria

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

    def unstructured_attributes(self, aviso_info):
        # This is a placeholder. You'll need to identify and extract unstructured text.
        # Example:
        unstructured_text = ""
        if "description" in aviso_info:
            unstructured_text += aviso_info["description"] + "\n"
        # You might also look for specific HTML snippets within aviso_info that contain unstructured text
        return {"unstructured_text": unstructured_text.strip()}
