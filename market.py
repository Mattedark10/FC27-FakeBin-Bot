import requests


class MarketClient:
    def __init__(self):
        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        })

        self.total_momentum = 0
        self.with_price = 0
        self.with_6h_history = 0

    def get_cards(self, ids=None, platform="ps"):

        # ==========================================
        # FUT.GG - 30 CARTE MOMENTUM
        # ==========================================

        futgg_url = (
            "https://www.fut.gg/api/fut/players/v2/27/"
        )

        params = {
            "hours": '"6"',
            "page": 1,
            "price__gte": 300000,
            "price__lte": 3000000
        }

        try:
            r = self.session.get(
                futgg_url,
                params=params,
                headers={
                    "Referer": (
                        "https://www.fut.gg/players/momentum/"
                        "?hours=%226%22&page=1"
                        "&price__gte=300000"
                        "&price__lte=3000000"
                    )
                },
                timeout=30
            )

            print("FUT.GG HTTP:", r.status_code)

            r.raise_for_status()

            data = r.json()

        except Exception as e:
            print("❌ Errore FUT.GG:", e)
            return []

        players = data.get("data", [])

        if not isinstance(players, list):
            players = []

        self.total_momentum = len(players)

        print(
            "Carte Momentum ricevute:",
            self.total_momentum
        )

        alerts = []

        print()
        print("========== CONTROLLO 6H ==========")

        # ==========================================
        # CONTROLLA STORICO PER OGNI EA ID
        # ==========================================

        for number, player in enumerate(players, 1):

            name = (
                player.get("commonName")
                or player.get("cardName")
                or "Unknown"
            )

            ea_id = player.get("eaId")

            if not ea_id:
                continue

            history_url = (
                f"https://fc27-market.val.run/"
                f"history/{ea_id}"
            )

            try:
                h = self.session.get(
                    history_url,
                    timeout=20
                )

                if not h.ok:
                    print(
                        f"{number}. {name} | "
                        f"History HTTP {h.status_code}"
                    )
                    continue

                history = h.json()

            except Exception as e:
                print(
                    f"{number}. {name} | "
                    f"Errore history: {e}"
                )
                continue

            timestamps = history.get("t", [])
            prices = history.get("p", [])

            if not prices:
                print(
                    f"{number}. {name} | "
                    "nessun prezzo"
                )
                continue

            current_price = prices[-1]

            if not current_price:
                continue

            self.with_price += 1

            # Il collector salva punti orari.
            # Per avere 6H servono almeno 7 punti:
            #
            # [-1] = adesso
            # [-7] = circa 6 ore prima

            if len(prices) < 7:

                print(
                    f"{number}. {name} | "
                    f"{current_price:,} | "
                    f"storico: {len(prices)} punti"
                )

                continue

            price_6h = prices[-7]

            if not price_6h:
                continue

            self.with_6h_history += 1

            change = (
                (current_price - price_6h)
                / price_6h
                * 100
            )

            print(
                f"{number}. {name} | "
                f"Now: {current_price:,} | "
                f"6H: {price_6h:,} | "
                f"{change:+.2f}%"
            )

            # ======================================
            # FILTRO PREZZO
            # ======================================

            if current_price < 300000:
                continue

            if current_price > 3000000:
                continue

            # ======================================
            # ALERT SOLO <= -5%
            # ======================================

            if change > -5:
                continue

            path = player.get("url", "")

            player_url = (
                "https://www.fut.gg" + path
                if path.startswith("/")
                else path
            )

            alerts.append({
                "id": player.get("id"),
                "ea_id": ea_id,
                "name": name,
                "overall": player.get("overall"),
                "rarity": player.get("rarityName"),

                "market_price": int(
                    current_price
                ),

                "reference_price": int(
                    price_6h
                ),

                "discount": abs(change),

                "momentum": change,

                "url": player_url
            })

        print("===================================")

        print()
        print("========== RISULTATO ==========")

        print(
            "Carte controllate:",
            self.total_momentum
        )

        print(
            "Con prezzo:",
            self.with_price
        )

        print(
            "Con storico 6H:",
            self.with_6h_history
        )

        print(
            "Occasioni <= -5%:",
            len(alerts)
        )

        print("===============================")

        return alerts