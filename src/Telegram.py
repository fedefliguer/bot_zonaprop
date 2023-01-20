import requests
import urllib.parse

class Telegram():
    def __init__(self, botId) -> None:
        self.botId = botId
    
    def get_chat_ids(self):
        updates_url = f"https://api.telegram.org/{self.botId}/getUpdates"
        req = requests.get(updates_url)
        ids = set()
        for chat in req.json()["result"]:
            ids.add((chat["message"]["from"]["username"], chat["message"]["chat"]["id"]))
        return ids
    
    def send_message(self, chatIds, message):
        encoded = urllib.parse.quote(message)
        chats = chatIds.split(",")
        for i in chats:
            url = f'https://api.telegram.org/{self.botId}/sendMessage?chat_id={i}&text={encoded}&parse_mode=HTML'
            requests.get(url)

    def make_message(self, post):
        message = f"""
        {post["titulo"]}\nPrecio: {post["precio"]}\nExpensas: {post["expensas"]}\nUbicacion: {post["ubicacion"]}\nLink: {post["url"]}"""
        return message
