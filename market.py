import requests
import json


class MarketClient:
    def __init__(self):
        self.session = requests.Session()

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

    def get_cards(self, ids=None, platform="ps"):

        url = "https://www.fut.gg/api/fut/players/v2/27/"

        params = {
            "hours": "6",
            "page": 1,
            "onlySpecialCards": "true",
            "price__gte": 300000
        }

        try:
            response = self.session.get(
                url,
                params=params,
                timeout=30
            )

            print("FUT.GG HTTP:", response.status_code)

            response.raise_for_status()
            data = response.json()

        except Exception as e:
            print("❌ Errore FUT.GG:", e)
            return []

        # Trova la lista delle carte
        players = None
        list_name = None

        if isinstance(data, dict):
            for key, value in data.items():
                if (
                    isinstance(value, list)
                    and len(value) > 0
                    and isinstance(value[0], dict)
                ):
                    players = value
                    list_name = key
                    break

        elif isinstance(data, list):
            players = data
            list_name = "root"

        if not players:
            print("❌ Nessuna carta trovata.")
            return []

        self.total_momentum = len(players)

        print("Lista trovata in:", list_name)
        print("Carte Momentum ricevute:", len(players))

        # ==========================================
        # DEBUG PRIMA CARTA
        # ==========================================

        print()
        print("========== DEBUG PRIMA CARTA ==========")

        try:
            print(
                json.dumps(
                    players[0],
                    indent=2,
                    ensure_ascii=False
                )
            )
        except Exception as e:
            print("Errore debug:", e)
            print(players[0])

        print("=======================================")
        print()

        # ==========================================
        # CHIAVI PRIMA CARTA
        # ==========================================

        if isinstance(players[0], dict):
            print("========== CHIAVI PRIMA CARTA ==========")

            for key in players[0].keys():
                print("-", key)

            print("========================================")
            print()

        # ==========================================
        # MOSTRA GLI ID
        # ==========================================

        print("========== ID CARTE ==========")

        for i, player in enumerate(players, 1):

            player_id = (
                player.get("id")
                or player.get("player_id")
                or player.get("ea_id")
            )

            print(f"{i}. ID: {player_id}")

        print("==============================")

        # Per adesso NON proviamo a inventare
        # prezzo/variazione 6h.
        #
        # Appena vediamo il JSON della prima carta
        # colleghiamo i campi corretti.
        return []