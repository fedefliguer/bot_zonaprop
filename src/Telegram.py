import requests
import urllib.parse

class Telegram():
    def __init__(self, botId) -> None:
        self.botId = botId
    
    def make_message(self, post):
        message = f"""
        {post["titulo"]}\nPrecio: {post["precio"]}\nExpensas: {post["expensas"]}\nUbicacion: {post["ubicacion"]}\nLink: {post["url"]}"""
        return message

    def send_message(self, chatIds, message):
        encoded = urllib.parse.quote(message)
        chats = chatIds.split(",")
        for i in chats:
            url = f'https://api.telegram.org/{self.botId}/sendMessage?chat_id={i}&text={encoded}&parse_mode=HTML'
            requests.get(url)

