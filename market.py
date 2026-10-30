import requests


class MarketClient:
    def __init__(self):
        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Referer": (
                "https://www.fut.gg/players/momentum/"
                '?hours=%226%22&page=1'
                "&onlySpecialCards=true"
                "&price__gte=300000"
            )
        })

        self.total_momentum = 0

    def get_cards(self, ids=None, platform="ps"):

        url = "https://www.fut.gg/api/fut/players/v2/27/"

        # IMPORTANTE:
        # FUT.GG usa hours="6", non hours=6
        params = {
            "hours": '"6"',
            "page": 1,
            "onlySpecialCards": "true",
            "price__gte": 300000,
        }

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
            print("❌ Errore FUT.GG:", e)
            return []

        # ==========================================
        # TROVA LISTA CARTE
        # ==========================================

        players = None

        if isinstance(data, dict):

            if isinstance(data.get("data"), list):
                players = data["data"]

            else:
                for value in data.values():
                    if (
                        isinstance(value, list)
                        and value
                        and isinstance(value[0], dict)
                    ):
                        players = value
                        break

        elif isinstance(data, list):
            players = data

        if not players:
            print("❌ Nessuna carta trovata")
            return []

        self.total_momentum = len(players)

        print("Carte Momentum ricevute:", len(players))

        # ==========================================
        # CONTROLLO CAMPI MOMENTUM
        # ==========================================

        print()
        print("========== MOMENTUM DATA ==========")

        valid = 0

        for i, player in enumerate(players, 1):

            name = (
                player.get("commonName")
                or player.get("cardName")
                or "Unknown"
            )

            player_id = player.get("id")

            price = player.get("currentDbPrice")
            momentum = player.get("momentumPercentage")

            print(
                f"{i}. {name} | "
                f"ID: {player_id} | "
                f"Price: {price} | "
                f"6H: {momentum}"
            )

            if price is not None and momentum is not None:
                valid += 1

        print("===================================")
        print("Carte con dati Momentum:", valid)
        print()

        # ==========================================
        # CREA ALERT
        # ==========================================

        cards = []

        for player in players:

            price = player.get("currentDbPrice")
            momentum = player.get("momentumPercentage")

            if price is None or momentum is None:
                continue

            try:
                price = int(price)
                momentum = float(momentum)
            except (TypeError, ValueError):
                continue

            # Fascia richiesta
            if price < 300000:
                continue

            if price > 3000000:
                continue

            # Ci interessano solo cali >= 5%
            if momentum > -5:
                continue

            name = (
                player.get("commonName")
                or player.get("cardName")
                or "Unknown"
            )

            # Se il prezzo è sceso del X%,
            # ricaviamo circa il prezzo precedente.
            #
            # Esempio:
            # 475k dopo -5% -> riferimento 500k

            multiplier = 1 + (momentum / 100)

            if multiplier <= 0:
                continue

            reference_price = int(
                price / multiplier
            )

            discount = abs(momentum)

            cards.append({
                "id": player.get("id"),
                "ea_id": player.get("eaId"),
                "name": name,
                "overall": player.get("overall"),
                "rarity": player.get("rarityName"),
                "market_price": price,
                "reference_price": reference_price,
                "discount": discount,
                "momentum": momentum,
                "url": (
                    "https://www.fut.gg"
                    + player.get("url", "")
                )
            })

        print("========== RISULTATO ==========")
        print("Carte controllate:", len(players))
        print("Carte >= -5%:", len(cards))
        print("===============================")

        return cards