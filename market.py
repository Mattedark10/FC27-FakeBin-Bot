import requests
import re
import time


class MarketClient:
    def __init__(self):
        self.session = requests.Session()

        # Header per API FUT.GG
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Referer": (
                "https://www.fut.gg/players/momentum/"
                "?hours=%226%22&page=1"
                "&onlySpecialCards=true"
                "&price__gte=300000"
            )
        })

        self.total_momentum = 0

    def get_momentum(self):

        url = "https://www.fut.gg/api/fut/players/v2/27/"

        params = {
            "hours": '"6"',
            "page": 1,
            "onlySpecialCards": "true",
            "price__gte": 300000
        }

        response = self.session.get(
            url,
            params=params,
            timeout=30
        )

        print("FUT.GG API HTTP:", response.status_code)
        print("FUT.GG API URL:", response.url)

        response.raise_for_status()

        data = response.json()

        players = data.get("data", [])

        self.total_momentum = len(players)

        print("Carte Momentum ricevute:", len(players))

        return players

    def check_player_page(self, player):

        path = player.get("url")

        if not path:
            return None

        url = "https://www.fut.gg" + path

        # IMPORTANTE:
        # non cambiamo gli header della sessione API.
        # Solo questa richiesta chiede HTML.
        response = self.session.get(
            url,
            headers={
                "Accept": "text/html,application/xhtml+xml"
            },
            timeout=30
        )

        name = (
            player.get("commonName")
            or player.get("cardName")
            or "Unknown"
        )

        if not response.ok:
            print(
                f"{name} | pagina HTTP: "
                f"{response.status_code}"
            )
            return None

        html = response.text

        # ==========================================
        # CERCA PREZZO
        # ==========================================

        price_patterns = [
            r'"currentDbPrice"\s*:\s*(\d+)',
            r'"currentDbPrice":(\d+)',
            r'"lowestBin"\s*:\s*(\d+)',
            r'"lowestBIN"\s*:\s*(\d+)',
            r'"lowestBinPrice"\s*:\s*(\d+)',
            r'"price"\s*:\s*(\d+)'
        ]

        price = None

        for pattern in price_patterns:
            match = re.search(pattern, html)

            if match:
                try:
                    value = int(match.group(1))

                    # Evita piccoli valori che potrebbero
                    # essere costi SBC/evoluzioni ecc.
                    if value >= 10000:
                        price = value
                        break

                except ValueError:
                    pass

        # ==========================================
        # CERCA MOMENTUM
        # ==========================================

        momentum_patterns = [
            r'"momentumPercentage"\s*:\s*(-?[\d.]+)',
            r'"momentumPercentage":(-?[\d.]+)',
            r'"momentum"\s*:\s*(-?[\d.]+)'
        ]

        momentum = None

        for pattern in momentum_patterns:
            match = re.search(pattern, html)

            if match:
                try:
                    momentum = float(match.group(1))
                    break
                except ValueError:
                    pass

        return {
            "id": player.get("id"),
            "ea_id": player.get("eaId"),
            "name": name,
            "overall": player.get("overall"),
            "rarity": player.get("rarityName"),
            "price": price,
            "momentum": momentum,
            "url": url
        }

    def get_cards(self, ids=None, platform="ps"):

        try:
            players = self.get_momentum()

        except Exception as e:
            print("❌ Errore Momentum:", e)
            return []

        print()
        print("========== TEST 30 CARTE ==========")

        cards_with_price = 0
        cards_with_momentum = 0
        cards_complete = 0

        alerts = []

        for i, player in enumerate(players, 1):

            try:
                result = self.check_player_page(player)

                if not result:
                    continue

                price = result["price"]
                momentum = result["momentum"]

                if price is not None:
                    cards_with_price += 1

                if momentum is not None:
                    cards_with_momentum += 1

                if (
                    price is not None
                    and momentum is not None
                ):
                    cards_complete += 1

                print(
                    f'{i}. {result["name"]} | '
                    f'Price: {price} | '
                    f'6H: {momentum}'
                )

                # Non possiamo creare alert
                # se manca uno dei due dati
                if price is None or momentum is None:
                    time.sleep(0.15)
                    continue

                # Prezzo 300k - 3M
                if price < 300000:
                    time.sleep(0.15)
                    continue

                if price > 3000000:
                    time.sleep(0.15)
                    continue

                # Deve essere scesa almeno del 5%
                if momentum > -5:
                    time.sleep(0.15)
                    continue

                # ==================================
                # PREZZO DI RIFERIMENTO
                # ==================================

                multiplier = 1 + (momentum / 100)

                if multiplier <= 0:
                    time.sleep(0.15)
                    continue

                reference = round(
                    price / multiplier
                )

                discount = abs(momentum)

                alerts.append({
                    "id": result["id"],
                    "ea_id": result["ea_id"],
                    "name": result["name"],
                    "overall": result["overall"],
                    "rarity": result["rarity"],
                    "market_price": price,
                    "reference_price": reference,
                    "discount": discount,
                    "momentum": momentum,
                    "url": result["url"]
                })

                time.sleep(0.15)

            except Exception as e:
                print(
                    f"{i}. ❌ Errore:",
                    type(e).__name__,
                    str(e)
                )

        print()
        print("========== RISULTATO TEST ==========")
        print("Carte controllate:", len(players))
        print("Con prezzo:", cards_with_price)
        print("Con Momentum:", cards_with_momentum)
        print("Con entrambi:", cards_complete)
        print("Alert >= -5%:", len(alerts))
        print("====================================")

        return alerts