import requests
import re
import time


class MarketClient:
    def __init__(self):
        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml",
        })

        self.total_momentum = 0

    def get_momentum(self):
        url = "https://www.fut.gg/api/fut/players/v2/27/"

        params = {
            "hours": '"6"',
            "page": 1,
            "onlySpecialCards": "true",
            "price__gte": 300000,
        }

        r = self.session.get(url, params=params, timeout=30)

        print("FUT.GG API HTTP:", r.status_code)

        r.raise_for_status()

        data = r.json()

        players = data.get("data", [])

        self.total_momentum = len(players)

        print("Carte Momentum:", len(players))

        return players

    def check_player_page(self, player):
        path = player.get("url")

        if not path:
            return None

        url = "https://www.fut.gg" + path

        r = self.session.get(url, timeout=30)

        name = (
            player.get("commonName")
            or player.get("cardName")
            or "Unknown"
        )

        if not r.ok:
            print(name, "| HTTP", r.status_code)
            return None

        html = r.text

        # Cerchiamo possibili dati prezzo presenti
        # direttamente nel codice della pagina.

        patterns = [
            r'"currentDbPrice"\s*:\s*(\d+)',
            r'"price"\s*:\s*(\d+)',
            r'"lowestBin"\s*:\s*(\d+)',
            r'"lowestBIN"\s*:\s*(\d+)',
            r'"lowestBinPrice"\s*:\s*(\d+)',
        ]

        price = None

        for pattern in patterns:
            match = re.search(pattern, html)

            if match:
                try:
                    price = int(match.group(1))
                    break
                except ValueError:
                    pass

        # Cerchiamo anche momentum
        momentum_patterns = [
            r'"momentumPercentage"\s*:\s*(-?[\d.]+)',
            r'"momentum"\s*:\s*(-?[\d.]+)',
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
            "url": url,
        }

    def get_cards(self, ids=None, platform="ps"):
        try:
            players = self.get_momentum()
        except Exception as e:
            print("❌ Errore Momentum:", e)
            return []

        print()
        print("========== TEST PAGINE ==========")

        found = []
        alerts = []

        for i, player in enumerate(players, 1):
            try:
                result = self.check_player_page(player)

                if not result:
                    continue

                price = result["price"]
                momentum = result["momentum"]

                print(
                    f'{i}. {result["name"]} | '
                    f'Price: {price} | '
                    f'6H: {momentum}'
                )

                if price is not None:
                    found.append(result)

                # Alert solo quando abbiamo ENTRAMBI
                if price is None or momentum is None:
                    continue

                if price < 300000 or price > 3000000:
                    continue

                if momentum > -5:
                    continue

                multiplier = 1 + momentum / 100

                if multiplier <= 0:
                    continue

                reference = int(price / multiplier)

                alerts.append({
                    "id": result["id"],
                    "name": result["name"],
                    "market_price": price,
                    "reference_price": reference,
                    "discount": abs(momentum),
                    "url": result["url"],
                })

                # Piccola pausa per non martellare FUT.GG
                time.sleep(0.15)

            except Exception as e:
                print(
                    f"{i}. Errore carta:",
                    type(e).__name__,
                    str(e)
                )

        print("=================================")
        print()
        print("Carte controllate:", len(players))
        print("Carte con prezzo trovato:", len(found))
        print("Alert >= -5%:", len(alerts))

        return alerts