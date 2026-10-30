import os
import requests


class TelegramAlert:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

        if not self.token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN mancante")

        if not self.chat_id:
            raise RuntimeError("TELEGRAM_CHAT_ID mancante")

    def send(self, text):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"

        response = requests.post(
            url,
            json={
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML"
            },
            timeout=20
        )

        if not response.ok:
            print("❌ Errore Telegram:")
            print(response.text)
            response.raise_for_status()

        print("✅ Messaggio Telegram inviato")
