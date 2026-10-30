import logging

from market import MarketClient
from telegram_alert import TelegramAlert


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

log = logging.getLogger("fc27-alert")


def run():

    print("================================")
    print("FC27 FUT.GG MOMENTUM BOT")
    print("================================")

    market = MarketClient()
    telegram = TelegramAlert()

    try:
        # Recupera Momentum 6H
        cards = market.get_cards()

        total = market.total_momentum
        opportunities = len(cards)

        print()
        print("========== RISULTATO ==========")
        print("Carte controllate:", total)
        print("Occasioni trovate:", opportunities)
        print("===============================")

        # ==========================================
        # NESSUNA OCCASIONE
        # ==========================================

        if opportunities == 0:

            message = (
                "🔎 <b>FC27 MARKET CHECK</b>\n\n"
                "📊 <b>Momentum:</b> 6H\n"
                "📄 <b>Pagina:</b> 1\n"
                "✨ <b>Carte:</b> Special\n"
                f"👀 <b>Carte controllate:</b> {total}\n"
                "📉 <b>Soglia alert:</b> -5%\n\n"
                "🚨 <b>Occasioni trovate:</b> 0\n\n"
                "✅ Controllo completato.\n"
                "Nessuna occasione trovata al momento."
            )

            telegram.send(message)

            print("✅ Report Telegram inviato")

            return

        # ==========================================
        # OCCASIONI TROVATE
        # ==========================================

        telegram.send(
            "🚨 <b>FC27 MARKET CHECK</b>\n\n"
            f"📊 Carte controllate: <b>{total}</b>\n"
            f"🔥 Occasioni trovate: <b>{opportunities}</b>"
        )

        for card in cards:

            name = card.get("name", "Unknown")
            price = card.get("market_price", 0)
            reference = card.get("reference_price", 0)
            discount = card.get("discount", 0)

            # Vendita ipotetica al prezzo reference
            after_tax = int(reference * 0.95)

            profit = after_tax - price

            message = (
                "🚨 <b>FC27 PRICE ALERT</b>\n\n"
                f"👤 <b>{name}</b>\n\n"
                f"💰 Market: <b>{price:,}</b>\n"
                f"📊 Reference: <b>{reference:,}</b>\n"
                f"📉 Difference: <b>-{discount:.2f}%</b>\n\n"
                f"💵 After EA tax: <b>{after_tax:,}</b>\n"
                f"✅ Potential profit: <b>{profit:,}</b>"
            )

            telegram.send(message)

        print("✅ Alert Telegram inviati")

    except Exception:

        log.exception("Errore durante il controllo")

        try:
            telegram.send(
                "❌ <b>FC27 BOT ERROR</b>\n\n"
                "Si è verificato un errore durante "
                "il controllo FUT.GG."
            )
        except Exception:
            pass

        raise


if __name__ == "__main__":
    run()