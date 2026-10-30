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

        # ==========================================
        # 1. PRENDE LE 30 CARTE MOMENTUM
        # ==========================================

        players_url = (
            "https://www.fut.gg/api/fut/players/v2/27/"
        )

        params = {
            "hours": '"6"',
            "page": 1,
            "price__gte": 300000,
            "price__lte": 3000000
        }

        try:
            response = self.session.get(
                players_url,
                params=params,
                timeout=30
            )

            print("========== MOMENTUM ==========")
            print("HTTP:", response.status_code)
            print("URL:", response.url)

            response.raise_for_status()

            data = response.json()

        except Exception as e:
            print("❌ Errore Momentum:", e)
            return []

        players = data.get("data", [])

        if not isinstance(players, list):
            players = []

        self.total_momentum = len(players)

        print("Carte ricevute:", len(players))
        print("==============================")
        print()

        if not players:
            return []

        # ==========================================
        # 2. PRENDE GLI EA ID
        # ==========================================

        ea_ids = []

        for player in players:

            ea_id = player.get("eaId")

            if ea_id is not None:
                ea_ids.append(str(ea_id))

        print("========== EA IDs ==========")

        for i, ea_id in enumerate(ea_ids, 1):
            print(f"{i}. {ea_id}")

        print("============================")
        print()

        if not ea_ids:
            print("❌ Nessun EA ID trovato")
            return []

        # ==========================================
        # 3. TEST API PREZZI
        # ==========================================

        print("========== TEST PLAYER-PRICES ==========")

        # Prima proviamo tutti gli ID insieme
        ids_string = ",".join(ea_ids)

        price_tests = [
            (
                "TEST A",
                "https://www.fut.gg/api/fut/player-prices/27/",
                {
                    "ids": ids_string
                }
            ),

            (
                "TEST B",
                "https://www.fut.gg/api/fut/player-prices/27/",
                {
                    "ids": ea_ids[0]
                }
            ),

            (
                "TEST C",
                (
                    "https://www.fut.gg/api/fut/"
                    f"player-prices/27/{ea_ids[0]}/"
                ),
                None
            )
        ]

        for test_name, url, test_params in price_tests:

            print()
            print("--------------------------------")
            print(test_name)
            print("--------------------------------")

            try:
                r = self.session.get(
                    url,
                    params=test_params,
                    timeout=30
                )

                print("HTTP:", r.status_code)
                print("URL:", r.url)
                print(
                    "Content-Type:",
                    r.headers.get("content-type")
                )

                # Non stampiamo una risposta gigantesca
                text = r.text

                print("Lunghezza risposta:", len(text))

                print()
                print("RISPOSTA:")
                print(text[:3000])

                # Se è JSON, mostriamo anche
                # la struttura principale
                try:
                    price_data = r.json()

                    print()
                    print("TIPO JSON:", type(price_data).__name__)

                    if isinstance(price_data, dict):

                        print(
                            "CHIAVI JSON:",
                            list(price_data.keys())
                        )

                        print()
                        print("JSON FORMATTATO:")

                        print(
                            json.dumps(
                                price_data,
                                indent=2,
                                ensure_ascii=False
                            )[:5000]
                        )

                    elif isinstance(price_data, list):

                        print(
                            "ELEMENTI JSON:",
                            len(price_data)
                        )

                        if price_data:
                            print()
                            print("PRIMO ELEMENTO:")

                            print(
                                json.dumps(
                                    price_data[0],
                                    indent=2,
                                    ensure_ascii=False
                                )[:5000]
                            )

                except Exception:
                    print("La risposta non è JSON.")

            except Exception as e:

                print(
                    "❌ Errore:",
                    type(e).__name__,
                    str(e)
                )

        print()
        print("========================================")
        print("TEST PREZZI COMPLETATO")
        print("========================================")

        # IMPORTANTE:
        # ancora nessun alert reale.
        return []