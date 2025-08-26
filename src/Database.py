# src/Database.py
import sqlite3
import datetime
import json

class Database:
    def __init__(self, db_name="listings.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        """
        Crea la tabla de propiedades si no existe.
        Contiene columnas clave para búsqueda y una para el JSON completo.
        """
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                processed_at TIMESTAMP,
                json_data TEXT
            )
        """)
        self.conn.commit()

    def add_property(self, url, json_structured_info):
        """Añade una nueva propiedad a la base de datos."""
        processed_at = datetime.datetime.now()
        # Convertimos el diccionario de Python a una cadena de texto JSON
        json_data_str = json.dumps(json_structured_info)

        self.cursor.execute("""
            INSERT INTO properties (url, processed_at, json_data)
            VALUES (?, ?, ?)
        """, (url, processed_at, json_data_str))
        self.conn.commit()

    def property_exists(self, url):
        """Verifica si una propiedad ya existe en la base de datos por su URL."""
        self.cursor.execute("SELECT id FROM properties WHERE url = ?", (url,))
        return self.cursor.fetchone() is not None

    def close(self):
        self.conn.close()
