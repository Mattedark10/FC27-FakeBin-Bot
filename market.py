import requests
import json


class MarketClient:
    def __init__(self):
        self.session = requests.Session()

        self.page_url = (
            "https://www.fut.gg/players/momentum/"
            "?hours=%226%22"
            "&page=1"
            "&price__gte=300000"
            "&price__lte=3000000"
        )

        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/141.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json",
            "Referer": self.page_url
        })

        self.total_momentum = 0

    def get_cards(self, ids=None, platform="ps"):

        url = "https://www.fut.gg/api/fut/players/v2/27/"

        # ESATTAMENTE i filtri del link FUT.GG
        params = {
            "hours": '"6"',
            "page": 1,
            "price__gte": 300000,
            "price__lte": 3000000
        }

        print("================================")
        print("FUT.GG MOMENTUM 6H")
        print("Prezzo: 300,000 - 3,000,000")
        print("Pagina: 1")
        print("================================")

        try:
            response = self.session.get(
                url,
                params=params,
                timeout=30
            )

            print("FUT.GG HTTP:", response.status_code)
            print("FUT.GG URL:", response.url)

            response.raise_for_status()

            data = response.json()

        except Exception as e:
            print("❌ Errore richiesta FUT.GG:", e)
            self.total_momentum = 0
            return []

        # ==========================================
        # TROVA LE CARTE
        # ==========================================

        players = []

        if isinstance(data, dict):

            if isinstance(data.get("data"), list):
                players = data["data"]

            else:
                for key, value in data.items():

                    if (
                        isinstance(value, list)
                        and value
                        and isinstance(value[0], dict)
                    ):
                        players = value
                        print("Lista trovata in:", key)
                        break

        elif isinstance(data, list):
            players = data

        self.total_momentum = len(players)

        print()
        print("Carte Momentum ricevute:", len(players))

        if not players:
            print("❌ Nessuna carta ricevuta.")
            return []

        # ==========================================
        # CONTROLLA I DATI RESTITUITI DA FUT.GG
        # ==========================================

        print()
        print("========== MOMENTUM 6H ==========")

        cards_with_price = 0
        cards_with_momentum = 0
        cards_complete = 0

        alerts = []

        for number, player in enumerate(players, start=1):

            if not isinstance(player, dict):
                continue

            name = (
                player.get("commonName")
                or player.get("cardName")
                or player.get("lastName")
                or "Unknown"
            )

            player_id = player.get("id")
            ea_id = player.get("eaId")

            price = player.get("currentDbPrice")
            momentum = player.get("momentumPercentage")

            # Alcune risposte potrebbero usare price
            # invece di currentDbPrice.
            if price is None:
                raw_price = player.get("price")

                if isinstance(raw_price, (int, float)):
                    price = raw_price

            if price is not None:
                cards_with_price += 1

            if momentum is not None:
                cards_with_momentum += 1

            if price is not None and momentum is not None:
                cards_complete += 1

            print(
                f"{number}. {name} | "
                f"ID: {player_id} | "
                f"EA ID: {ea_id} | "
                f"Price: {price} | "
                f"6H: {momentum}"
            )

            # ======================================
            # SERVONO PREZZO + MOMENTUM
            # ======================================

            if price is None or momentum is None:
                continue

            try:
                price = int(float(price))
                momentum = float(momentum)

            except (TypeError, ValueError):
                print(
                    f"⚠️ Dati non validi per {name}: "
                    f"{price} / {momentum}"
                )
                continue

            # ======================================
            # PREZZO 300K - 3M
            # ======================================

            if price < 300000:
                continue

            if price > 3000000:
                continue

            # ======================================
            # CALO MINIMO -5%
            # ======================================

            if momentum > -5:
                continue

            # Esempio:
            # prezzo attuale 475k
            # momentum -5%
            #
            # riferimento ≈ 500k

            multiplier = 1 + (momentum / 100)

            if multiplier <= 0:
                continue

            reference_price = round(
                price / multiplier
            )

            discount = abs(momentum)

            player_path = player.get("url", "")

            if player_path.startswith("/"):
                player_url = (
                    "https://www.fut.gg"
                    + player_path
                )
            else:
                player_url = player_path

            alerts.append({
                "id": player_id,
                "ea_id": ea_id,
                "name": name,
                "overall": player.get("overall"),
                "rarity": player.get("rarityName"),
                "market_price": price,
                "reference_price": reference_price,
                "discount": discount,
                "momentum": momentum,
                "url": player_url
            })

        print("=================================")

        # ==========================================
        # RISULTATO
        # ==========================================

        print()
        print("========== RISULTATO ==========")
        print(
            "Carte controllate:",
            self.total_momentum
        )
        print(
            "Con prezzo:",
            cards_with_price
        )
        print(
            "Con Momentum 6H:",
            cards_with_momentum
        )
        print(
            "Con entrambi:",
            cards_complete
        )
        print(
            "Occasioni <= -5%:",
            len(alerts)
        )
        print("===============================")

        return alerts