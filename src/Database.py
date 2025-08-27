# src/Database.py
import psycopg2
import datetime
import json
import os

class Database:
    def __init__(self):
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise ValueError("No se encontró la variable de entorno DATABASE_URL")
        
        self.conn = psycopg2.connect(db_url)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        """
        Crea la tabla de propiedades si no existe.
        Usa tipos de datos compatibles con PostgreSQL.
        """
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id SERIAL PRIMARY KEY,
                url TEXT NOT NULL UNIQUE,
                processed_at TIMESTAMPA,
                json_data JSONB
            )
        """)
        self.conn.commit()

    def add_property(self, url, json_structured_info):
        """Añade una nueva propiedad a la base de datos."""
        processed_at = datetime.datetime.now()
        # psycopg2 puede manejar la conversión de dict a JSONB directamente
        json_data = json.dumps(json_structured_info)

        self.cursor.execute("""
            INSERT INTO properties (url, processed_at, json_data)
            VALUES (%s, %s, %s)
        """, (url, processed_at, json_data))
        self.conn.commit()

    def property_exists(self, url):
        """Verifica si una propiedad ya existe en la base de datos por su URL."""
        self.cursor.execute("SELECT id FROM properties WHERE url = %s", (url,))
        return self.cursor.fetchone() is not None

    def close(self):
        self.conn.close()
