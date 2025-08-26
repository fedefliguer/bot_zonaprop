# src/Telegram.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

class TelegramNotifier:
    def __init__(self):
        """
        Inicializa el notificador con el token del bot y el ID del chat 
        desde las variables de entorno.
        """
        self.token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.environ.get("CHAT_ID")
        if not self.token or not self.chat_id:
            raise ValueError("Las variables de entorno TELEGRAM_BOT_TOKEN y CHAT_ID deben estar definidas.")

    def send_message(self, message):
        """
        Envía un mensaje de texto al chat de Telegram configurado.
        """
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        params = {
            "chat_id": self.chat_id,
            "text": message
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()  # Lanza un error para respuestas 4xx/5xx
            print("✅ Mensaje enviado a Telegram correctamente.")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error al enviar mensaje a Telegram: {e}")
            return None
