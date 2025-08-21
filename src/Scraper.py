# scraper.py
from bs4 import BeautifulSoup
import re
import json
from typing import Any, Dict, List, Union, Optional

class Scraper:
    """
    A class to handle scraping a single Zonaprop listing and checking its details,
    as well as scraping multiple listings from a search results page.
    """
    base_url = "https://www.zonaprop.com.ar"
    PAGE_URL_SUFFIX = '-pagina-'
    HTML_EXTENSION = '.html'

    def __init__(self, browser_instance, scrape_url: Optional[str] = None) -> None:
        """Initializes the scraper with a Browser instance."""
        self.browser = browser_instance
        self.scrape_url = scrape_url
        self.avenidas_caba = ["corrientes", "libertador", "santa fe", "cordoba", "rivadavia", "cabildo", "lacroze", "juan b justo", "constitucion", "callao", "entre rios", "general paz"]

    # Methods for a single listing
    def reduce_html_to_aviso_info(self, html_text: str) -> Optional[Dict[str, Any]]:
        """
        Searches the HTML for a block: const avisoInfo = { ... };
        """
        if not html_text:
            return None

        match = re.search(r"const\s+avisoInfo\s*=\s*(\{[\s\S]*?\});", html_text, re.DOTALL)
        if not match:
            return None

        raw_obj = match.group(1).strip()

        # Clean similar to reduce.py
        # 1) Remove trailing commas before ] or }
        cleaned = re.sub(r",\s*([\}\]])", r"\1", raw_obj)
        # 2) Remove single-line comments //
        cleaned = re.sub(r"//.*$", "", cleaned, flags=re.MULTILINE)
        # 3) Add quotes to unquoted keys (heuristic)
        cleaned = re.sub(r'(\w+)\s*:', r'"\1":', cleaned)

        # Remove the final semicolon if it remains
        if cleaned.endswith(';'):
            cleaned = cleaned[:-1].rstrip()

        return cleaned

    def parse_number_from_text(self, text: Union[str, int]) -> int:
        """
        Parses a number from a text string, handling common formats.
        """
        text = str(text)
        if not text:
            return 0
        cleaned_text = re.sub(r'[$,.]', '', text.strip())
        number_match = re.search(r'(\d+)', cleaned_text)
        return int(number_match.group(1)) if number_match else 0
    
    def structured_attributes(self, aviso_info_str: str) -> str:
        """
        Extracts structured attributes from the avisoInfo string.
        """
        structured = {}
        
        # Patterns for each attribute.
        patrones = {
            "id": r"'idAviso':\s*['\"](.*?)['\"]",
            "title": r"'postingTitle'\s*:\s*['\"](.*?)['\"]",
            "price": r"'price'\s*:\s*['\"](.*?)['\"]",
            "expenses": r"'expenses'\s*:\s*['\"](.*?)['\"]",
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
                        # Replace single with double quotes and fix syntax
                        temp_json_str = value.replace("'", '"')
                        temp_json_str = re.sub(r'\"(null|false|true)\"', r'\1', temp_json_str)
                        
                        parsed_json = json.loads(temp_json_str)
                        structured[key] = parsed_json
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON for {key}: {e}")
                        structured[key] = value
                else:
                    structured[key] = value
        
        # Additional cleaning for description
        if "description" in structured:
            clean_description = re.sub(r'<[^>]+>', '', structured["description"])
            structured["description"] = clean_description.replace("&quot;", '"').strip()

        return json.dumps(structured, indent=2, ensure_ascii=False)

    def extract_data(self, soup):
        container = soup.find("div", {"class":"postings-container"})
        return container

    def scrape_web(self) -> List[str]:
        """
        Scrapes a search results page and extracts exactly the seven property URLs
        from the mainEntity list within the preloadedData block.
        """
        if not self.scrape_url:
            raise ValueError("scrape_url must be provided to use scrape_web method.")

        page_url = f"{self.scrape_url}{self.HTML_EXTENSION}"
        page = self.browser.get_text(page_url)
        
        # Define la función slice_preloaded_block como la tenías
        def slice_preloaded_block(raw_html: str) -> str:
            """Devuelve el <script id='preloadedData'>...</script> completo, o ''."""
            m = re.search(
                r'<script[^>]*\bid=["\']preloadedData["\'][^>]*>.*?</script>',
                raw_html, flags=re.DOTALL | re.IGNORECASE
            )
            return m.group(0) if m else ""

        html_string = slice_preloaded_block(page)
        
        # --- Modificación: Expresión regular más específica ---
        # El nuevo patrón busca específicamente las URLs dentro del bloque "mainEntity"
        # que es la lista de 7 elementos que quieres.
        pattern = re.compile(r'\"mainEntity\":\[.*?(\"url\":\".*?\".*?){7}\]', re.DOTALL)
        
        match = pattern.search(html_string)
        if match:
            # Encuentra todas las URLs dentro de la coincidencia
            url_pattern = re.compile(r'"url":"(.*?)"')
            urls = url_pattern.findall(match.group(0))
            return urls
        
        return []
