# Checker.py
from typing import Dict, Any, Tuple
import re

class Checker:
    """
    Una clase para evaluar si un aviso de propiedad cumple con ciertos criterios deseables.
    """
    def __init__(self, structured_data: Dict[str, Any]):
        """Inicializa el checker con los datos estructurados del aviso."""
        self.data = structured_data
        self.results = []
        self.counts = {"✅": 0, "❌": 0, "❓": 0}
        self.avenidas_caba = ["av. ", "av ", "avenida "]
        self.orientacion_check = ["Norte", "Noreste", "Noroeste", "N", "NE", "NO"]
        self.orientacion_question = ["Este", "Oeste", "E", "O"]
        self.orientacion_cross = ["Sur", "Sudeste", "Sudoeste", "S", "SO", "SE"]

    def _check_condition(self, condition: Any, requirement_name: str, explanation: str):
        """Añade un resultado de chequeo a la lista de resultados y actualiza los contadores."""
        emoji = "❓"
        if condition is True:
            emoji = "✅"
        elif condition is False:
            emoji = "❌"
        
        self.results.append(f"{emoji} {requirement_name}: {explanation}")
        self.counts[emoji] += 1

    def run_checks(self):
        """
        Ejecuta todos los chequeos definidos y almacena los resultados.
        """
        self.check_bathrooms()
        self.check_age()
        self.check_covered_area()
        self.check_balcony_or_patio()
        self.check_laundry()
        self.check_gas()
        self.check_expensas()
        self.check_address()
        self.check_orientation()
        self.check_elevator_and_floor()

    def check_elevator_and_floor(self):
        """Chequea si el departamento tiene ascensor y está en un piso superior al 4to."""
        general_features = self.data.get("general_features", {})
        has_elevator = False
        if "Servicios" in general_features:
            for feature in general_features["Servicios"].values():
                if feature.get("label") == "Ascensor":
                    has_elevator = True
                    break
        
        description_text = self.data.get("description", "").lower()
        if "ascensor" in description_text:
            has_elevator = True

        floor_number = None
        if "floor" in self.data and self.data["floor"] is not None:
            floor_str = str(self.data["floor"])
            floor_numbers = re.findall(r'\d+', floor_str)
            if floor_numbers:
                floor_number = int(floor_numbers[0])

        if has_elevator and floor_number is not None and floor_number > 4:
            self._check_condition(True, "Ascensor y piso", f"Tiene ascensor y está en el piso {floor_number}.")
        elif not has_elevator and floor_number is not None and floor_number in [2, 3]:
            self._check_condition(False, "Ascensor y piso", f"Piso {floor_number} por escalera.")
        else:
            explanation = "No se pudo determinar la información del ascensor y el piso."
            if has_elevator:
                explanation = "Tiene ascensor pero no se pudo determinar el piso."
            if floor_number is not None:
                explanation = f"Piso {floor_number} pero no se pudo determinar si tiene ascensor."
            self._check_condition(None, "Ascensor y piso", explanation)

    def check_bathrooms(self):
        """Chequea si el aviso tiene 2 baños o más."""
        try:
            bathrooms = int(self.data.get("bathrooms", 0))
            condition = bathrooms >= 2
            explanation = f"Tiene {bathrooms} baño{'s' if bathrooms != 1 else ''}. "
            self._check_condition(condition, "Tiene dos baños o más", explanation)
        except (ValueError, TypeError):
            self._check_condition(False, "Tiene dos baños o más", "No se pudo determinar la cantidad de baños.")

    def check_age(self):
        """Chequea si la antigüedad es menor a 50 años."""
        try:
            antiquity_data = self.data.get("main_features", {}).get("CFT5")
            if antiquity_data and antiquity_data.get("label") == "antigüedad":
                age = int(antiquity_data.get("value"))
                condition = age < 50
                explanation = f"Antigüedad de {age} años."
                self._check_condition(condition, "Antigüedad menor a 50 años", explanation)
            else:
                self._check_condition(None, "Antigüedad menor a 50 años", "No se encontró la antigüedad del inmueble.")
        except (KeyError, ValueError, TypeError):
            self._check_condition(None, "Antigüedad menor a 50 años", "No se pudo determinar la antigüedad.")

    def check_covered_area(self):
        """Chequea si tiene más de 60m2 cubiertos."""
        try:
            covered_area = int(self.data.get("surface_covered", 0))
            condition = covered_area > 60
            explanation = f"Tiene {covered_area}m² cubiertos."
            self._check_condition(condition, "Más de 60m² cubiertos", explanation)
        except (ValueError, TypeError):
            self._check_condition(False, "Más de 60m² cubiertos", "No se pudo determinar la superficie cubierta.")

    def check_balcony_or_patio(self):
        """Chequea si tiene balcón, patio o más m2 totales que cubiertos."""
        has_balcony_general = any(item.get("label") == "Balcón" for item in self.data.get("general_features", {}).get("Ambientes", {}).values())
        description_text = self.data.get("description", "").lower()
        has_balcony_description = "balcón" in description_text
        has_patio_description = "patio" in description_text

        has_balcony_or_patio = has_balcony_general or has_balcony_description or has_patio_description
        total_area = int(self.data.get("surface_total", 0))
        covered_area = int(self.data.get("surface_covered", 0))
        has_extra_space = total_area > covered_area

        condition = has_balcony_or_patio or has_extra_space
        explanation = ""
        if condition:
            if has_balcony_or_patio:
                explanation += "Se menciona balcón o patio."
            if has_extra_space:
                explanation += f" Los m² totales ({total_area}) son mayores que los cubiertos ({covered_area})."
        else:
            explanation = f"No tiene balcón/patio y los m² totales ({total_area}) son iguales o menores que los cubiertos ({covered_area})."
        
        self._check_condition(condition, "Balcón, patio, o más m² totales que cubiertos", explanation.strip())

    def check_laundry(self):
        """Chequea si tiene lavadero."""
        has_laundry_general = any(item.get("label") == "Lavadero" for item in self.data.get("general_features", {}).get("Ambientes", {}).values())
        description_text = self.data.get("description", "").lower()
        has_laundry_description = "lavadero" in description_text

        condition = has_laundry_general or has_laundry_description
        explanation = "Se encontró la palabra 'lavadero'." if condition else "No se encontró la palabra 'lavadero'."
        self._check_condition(condition, "Tiene lavadero", explanation)

    def check_gas(self):
        """Chequea si tiene gas o cocina a gas."""
        description_text = self.data.get("description", "").lower()
        if "cocina a gas" in description_text or "gas" in description_text:
            self._check_condition(True, "Tiene gas", "Se menciona gas o cocina a gas en la descripción.")
        else:
            self._check_condition(None, "Tiene gas", "No se pudo confirmar si tiene gas.")

    def check_expensas(self):
        """Chequea si las expensas son menores a $150.000."""
        # Prioridad 1: Campo 'expenses' del avisoInfo
        expensas_value = self.data.get("expenses")
        
        if expensas_value:
            try:
                expensas = int(expensas_value)
                condition = expensas < 150000
                explanation = f"Expensas de ${expensas:,}. "
                self._check_condition(condition, "Expensas menores a $150.000", explanation)
                return
            except (ValueError, TypeError):
                # Si el campo existe pero no es un número válido, se sigue a la siguiente lógica
                pass

        # Prioridad 2: Buscar en la descripción
        description_text = self.data.get("description", "").lower()
        match = re.search(r'expensas.*?(\$?\s*\d[\d\.,]*)', description_text, re.IGNORECASE)
        
        if match:
            expensas_str = match.group(1).replace(' ', '').replace('.', '').replace(',', '').strip()
            try:
                expensas = int(expensas_str)
                condition = expensas < 150000
                explanation = f"Expensas de ${expensas:,}. "
                self._check_condition(condition, "Expensas menores a $150.000", explanation)
            except ValueError:
                self._check_condition(None, "Expensas menores a $150.000", "No se pudo extraer un valor numérico de las expensas.")
        else:
            self._check_condition(None, "Expensas menores a $150.000", "No se encontró la palabra 'expensas' en la descripción.")

    def check_address(self):
        """Chequea si el inmueble está en una avenida y su disposición."""
        address = self.data.get("address", "").lower()
        disposicion = self.data.get("main_features", {}).get("1000019", {}).get("value", "").lower()

        is_on_avenue = any(avenida in address for avenida in self.avenidas_caba)

        if is_on_avenue:
            if disposicion == "contrafrente":
                self._check_condition(None, "No está en una avenida", f"Es contrafrente, aunque la dirección {address} esté en una avenida.")
            else:
                self._check_condition(False, "No está en una avenida", f"La dirección {address} está en una avenida y no es contrafrente.")
        else:
            self._check_condition(True, "No está en una avenida", f"La dirección {address} no está en una avenida.")

    def check_orientation(self):
        """Chequea la orientación del inmueble."""
        orientation = self.data.get("main_features", {}).get("1000029", {}).get("value")
        
        if orientation in self.orientacion_check:
            self._check_condition(True, "Orientación", f"Orientación {orientation}, buena luminosidad.")
        elif orientation in self.orientacion_question:
            self._check_condition(None, "Orientación", f"Orientación {orientation}, luminosidad intermedia.")
        elif orientation in self.orientacion_cross:
            self._check_condition(False, "Orientación", f"Orientación {orientation}, poca luminosidad.")
        else:
            self._check_condition(None, "Orientación", "No se pudo determinar la orientación.")

    def get_results(self) -> str:
        """Devuelve los resultados de los chequeos como una cadena de texto."""
        # Se agrega la información de precio y editor al final
        publisher_name = self.data.get("publisher_name", "No disponible")
        publisher_whatsapp = self.data.get("whatsapp", "No disponible")
        
        end_info = f"\nPrecio: {self.data.get('price', 'No disponible')} ({self.data.get('currency', 'N/A')})"
        end_info += f"\nPublicado por: {publisher_name}"
        if publisher_whatsapp:
            end_info += f"\nWhatsApp: {publisher_whatsapp}"

        return "\n".join(self.results) + end_info
    
    def get_counts(self) -> Tuple[int, int, int]:
        """Devuelve la cantidad de checks positivos, dudosos y negativos."""
        return self.counts["✅"], self.counts["❓"], self.counts["❌"]
