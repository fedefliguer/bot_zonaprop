# Checker.py
from typing import Dict, Any, List, Tuple
import re

class Checker:
    """
    Evalúa si una propiedad cumple con criterios específicos, agrupados por antigüedad.
    """
    def __init__(self, structured_data: Dict[str, Any]):
        self.data = structured_data
        self.results = []
        self.property_type = "Desconocido"
        self.passed_checks_list = []
        self.failed_checks_list = []
        self.unknown_checks_list = []
        self.avenidas_principales = [
            "av.", "avenida", "av:",
            "del libertador", "corrientes", "córdoba", "santa fe", "rivadavia", 
            "callao", "pueyrredón", "las heras", "coronel díaz", "cabildo", "pueyrredon",
            "juramento", "congreso", "triunvirato", "de los incas", "álvarez thomas",
            "forest", "federico lacroze", "gaona", "nazca", "san martín", "san martin",
            "beiró", "lope de vega", "juan b. justo", "acoyte", "la plata", "directorio",
            "eva perón", "san juan", "independencia", "belgrano", "entre ríos", "jujuy"
        ]

    def _add_result(self, status: str, check_name: str, details: str):
        """Añade un resultado a las listas de checks pasados, fallidos o desconocidos."""
        if status == "passed":
            self.passed_checks_list.append(f"✅ {check_name}: {details}")
        elif status == "failed":
            self.failed_checks_list.append(f"❌ {check_name}: {details}")
        else: # unknown
            self.unknown_checks_list.append(f"🟡 {check_name}: {details}")

    def run_all_checks(self):
        """
        Ejecuta todos los chequeos basados en la antigüedad y los requisitos generales.
        """
        # 1. Determinar el grupo de antigüedad
        age = self._get_age()
        price = self._get_price()

        if age is not None:
            if 0 <= age <= 20:
                self.property_type = "Nuevo (0-20 años)"
                self._run_nuevos_checks(price)
            elif 21 <= age <= 50:
                self.property_type = "Intermedio (21-50 años)"
                self._run_intermedios_checks(price)
            else: # > 50
                self.property_type = "Viejo (+50 años)"
                self._run_viejos_checks(price)
        else:
            self.property_type = "Antigüedad desconocida"
            # No se pueden correr checks específicos de grupo, pero sí los generales.

        # 2. Ejecutar chequeos comunes a todos los grupos
        self._check_common_requirements()

    def _get_age(self) -> int | None:
        """Extrae la antigüedad del inmueble."""
        try:
            # Intenta obtener la antigüedad desde 'main_features'
            antiquity_data = self.data.get("main_features", {}).get("CFT5")
            if antiquity_data and antiquity_data.get("label") == "antigüedad":
                return int(antiquity_data.get("value"))
            
            # Si no, busca en la descripción
            description = self.data.get("description", "").lower()
            match = re.search(r'(\d+)\s+años\s+de\s+antigüedad', description)
            if match:
                return int(match.group(1))

        except (KeyError, ValueError, TypeError):
            pass
        return None

    def _get_price(self) -> float | None:
        """Extrae el precio del inmueble."""
        try:
            price_str = self.data.get("price")
            currency = self.data.get("currency")
            if price_str and currency == "USD":
                # Eliminar "USD" y puntos de miles, luego convertir a float
                price_cleaned = re.sub(r'[USD\s,.]', '', price_str)
                return float(price_cleaned)
        except (ValueError, TypeError):
            pass
        return None
    
    def _get_floor(self) -> int | None:
        """Extrae el número de piso del inmueble."""
        try:
            floor_str = str(self.data.get("floor", ""))
            floor_numbers = re.findall(r'\\d+', floor_str)
            if floor_numbers:
                return int(floor_numbers[0])
        except (ValueError, TypeError):
            pass
        return None

    # --- CHEQUEOS COMUNES ---
    def _check_common_requirements(self):
        """Chequeos que aplican a todos los inmuebles."""
        self._check_bathrooms()
        self._check_balcony_or_patio()
        self._check_expensas()
        self._check_avenue()

    def _check_bathrooms(self):
        """Chequea si tiene 2 o más baños."""
        try:
            bathrooms = int(self.data.get("bathrooms", 0))
            if bathrooms > 0:
                passed = bathrooms >= 2
                self._add_result("passed" if passed else "failed", "Baños", f"Tiene {bathrooms} baño(s).")
            else:
                self._add_result("unknown", "Baños", "No se pudo determinar la cantidad.")
        except (ValueError, TypeError):
            self._add_result("unknown", "Baños", "No se pudo determinar la cantidad.")

    def _check_balcony_or_patio(self):
        """Chequea si tiene balcón o patio."""
        has_balcony = any(item.get("label") == "Balcón" for item in self.data.get("general_features", {}).get("Ambientes", {}).values())
        description = self.data.get("description", "").lower()
        has_balcony_desc = "balcón" in description
        has_patio_desc = "patio" in description
        
        if has_balcony or has_balcony_desc or has_patio_desc:
            self._add_result("passed", "Balcón o Patio", "Sí")
        else:
            self._add_result("unknown", "Balcón o Patio", "No especificado.")

    def _check_expensas(self):
        """Chequea si las expensas son menores a $150,000."""
        expensas_val = self.data.get("expenses")
        if expensas_val:
            try:
                expensas = int(expensas_val)
                passed = expensas < 150000
                self._add_result("passed" if passed else "failed", "Expensas", f"Son de ${expensas:,}.")
                return
            except (ValueError, TypeError):
                pass
        self._add_result("unknown", "Expensas", "No especificadas.")

    def _check_avenue(self):
        """Chequea si la dirección está en una avenida principal."""
        address = self.data.get("address", "").lower()
        if not address or address == 'n/a':
            self._add_result("unknown", "No en Avenida", "Dirección no especificada.")
            return

        is_on_avenue = any(av in address for av in self.avenidas_principales)
        passed = not is_on_avenue
        details = f"Dirección: {self.data.get('address', 'N/A')}."
        self._add_result("passed" if passed else "failed", "No en Avenida", details)

    # --- CHEQUEOS POR GRUPO ---
    def _run_nuevos_checks(self, price: float | None):
        """Chequeos para inmuebles 'Nuevos' (0-20 años)."""
        # Precio
        if price is not None:
            passed = price <= 160000
            self._add_result("passed" if passed else "failed", "Precio (Max $160k)", f"USD ${price:,.0f}.")
        else:
            self._add_result("unknown", "Precio (Max $160k)", "No especificado.")
        
        # Gas
        description = self.data.get("description", "").lower()
        has_gas = "cocina a gas" in description or "gas natural" in description
        if has_gas:
            self._add_result("passed", "Tiene Gas", "Sí")
        else:
            self._add_result("unknown", "Tiene Gas", "No especificado.")

        # Ascensor o 1er piso
        has_elevator = "ascensor" in description or any(f.get("label") == "Ascensor" for f in self.data.get("general_features", {}).get("Servicios", {}).values())
        floor = self._get_floor()
        
        if floor is not None:
            is_first_floor = floor == 1
            passed_elevator = has_elevator or is_first_floor
            details = f"Piso: {floor}. Ascensor: {'Sí' if has_elevator else 'No'}."
            self._add_result("passed" if passed_elevator else "failed", "Ascensor o 1er Piso", details)
        else:
            details = f"Piso: N/A. Ascensor: {'Sí' if has_elevator else 'No'}."
            self._add_result("unknown", "Ascensor o 1er Piso", details)


    def _run_intermedios_checks(self, price: float | None):
        """Chequeos para inmuebles 'Intermedios' (20-50 años)."""
        # Precio
        if price is not None:
            passed = price <= 145000
            self._add_result("passed" if passed else "failed", "Precio (Max $145k)", f"USD ${price:,.0f}.")
        else:
            self._add_result("unknown", "Precio (Max $145k)", "No especificado.")

        # No primer piso
        floor = self._get_floor()
        if floor is not None:
            not_first_floor = floor != 1
            self._add_result("passed" if not_first_floor else "failed", "No es 1er Piso", f"Piso: {floor}.")
        else:
            self._add_result("unknown", "No es 1er Piso", "Piso: N/A.")

        # Luminoso
        description = self.data.get("description", "").lower()
        is_luminous = "luminoso" in description or "mucha luz" in description
        if is_luminous:
            self._add_result("passed", "Luminoso", "Sí")
        else:
            self._add_result("unknown", "Luminoso", "No especificado.")

    def _run_viejos_checks(self, price: float | None):
        """Chequeos para inmuebles 'Viejos' (+50 años)."""
        # Precio
        if price is not None:
            passed = price <= 130000
            self._add_result("passed" if passed else "failed", "Precio (Max $130k)", f"USD ${price:,.0f}.")
        else:
            self._add_result("unknown", "Precio (Max $130k)", "No especificado.")

        # No primer piso
        floor = self._get_floor()
        if floor is not None:
            not_first_floor = floor != 1
            self._add_result("passed" if not_first_floor else "failed", "No es 1er Piso", f"Piso: {floor}.")
        else:
            self._add_result("unknown", "No es 1er Piso", "Piso: N/A.")

        # Luminoso
        description = self.data.get("description", "").lower()
        is_luminous = "luminoso" in description or "mucha luz" in description
        if is_luminous:
            self._add_result("passed", "Luminoso", "Sí")
        else:
            self._add_result("unknown", "Luminoso", "No especificado.")

    def get_summary(self) -> str:
        """Devuelve un resumen formateado de los resultados."""
        summary_lines = [
            f"🏠 Tipo: {self.property_type}",
            f"📍 Dirección: {self.data.get('address', 'No disponible')}",
        ]
        summary_lines.extend(self.passed_checks_list)
        
        if self.failed_checks_list:
            summary_lines.extend(self.failed_checks_list)
        
        if self.unknown_checks_list:
            summary_lines.extend(self.unknown_checks_list)
            
        return "\n".join(summary_lines)

    def passed_avenue_check(self) -> bool:
        """Verifica si el chequeo de la avenida fue exitoso."""
        for result in self.passed_checks_list:
            if "No en Avenida" in result:
                return True
        return False

    def passed_price_check(self) -> bool:
        """Verifica si el chequeo de precio fue exitoso."""
        for result in self.passed_checks_list:
            if "Precio" in result:
                return True
        return False
