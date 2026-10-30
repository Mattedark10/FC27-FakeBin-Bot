import json
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from market import MarketClient
from telegram_alert import TelegramAlert

DROP_PERCENT = 5.0
STATE_FILE = Path("state.json")

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("fc27-alert")


def load_state():
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.exists() else {}
    except Exception:
        return {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def run_once():
    market = MarketClient()
    telegram = TelegramAlert()
    state = load_state()
    cards = market.get_cards(platform="ps")
    active = set()

    for card in cards:
        change = card["change_6h"]
        if change > -DROP_PERCENT:
            continue

        key = card["id"]
        active.add(key)
        price = card["market_price"]

        # Prezzo stimato 6h fa ricavato dalla variazione percentuale.
        denominator = 1 + (change / 100)
        reference = round(price / denominator) if denominator > 0 else price
        after_tax = int(reference * 0.95)
        profit = after_tax - price

        old = state.get(key)
        # Un alert quando entra nella soglia; nuovo alert solo se il prezzo scende ancora.
        if old and price >= int(old.get("market_price", 0)):
            continue

        telegram.send(
            "🚨 <b>FC27 MOMENTUM ALERT</b>\n\n"
            f"👤 <b>{card['name']}</b>\n"
            f"💰 Prezzo FUT.GG: <b>{price:,}</b>\n"
            f"🕕 Stima 6h fa: <b>{reference:,}</b>\n"
            f"📉 Variazione 6h: <b>{change:.2f}%</b>\n"
            f"💵 Vendita dopo tassa 5%: <b>{after_tax:,}</b>\n"
            f"✅ Profitto potenziale: <b>{profit:,}</b>"
        )
        state[key] = {"market_price": price, "change_6h": round(change, 2)}

    # Se una carta non è più sotto -5%, può generare un nuovo alert in futuro.
    for key in list(state):
        if key not in active:
            state.pop(key, None)

    save_state(state)
    print(f"Controllo completato. Alert attivi nello state: {len(state)}")


if __name__ == "__main__":
    try:
        run_once()
    except Exception:
        log.exception("Errore durante il controllo")
        raise
