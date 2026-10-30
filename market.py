import requests


class MarketClient:
    FUTGG_URL = "https://www.fut.gg/api/fut/players/v2/27/"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/130 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.fut.gg/players/momentum/?hours=%226%22&page=1&onlySpecialCards=true&price__gte=300000",
        })

    @staticmethod
    def _num(value):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        if isinstance(value, str):
            s = value.strip().replace(",", "").replace("%", "")
            try:
                return float(s)
            except ValueError:
                return None
        return None

    @classmethod
    def _find_value(cls, obj, keys):
        """Cerca ricorsivamente la prima chiave utile anche dentro oggetti annidati."""
        if isinstance(obj, dict):
            lowered = {str(k).lower(): v for k, v in obj.items()}
            for key in keys:
                if key.lower() in lowered:
                    value = lowered[key.lower()]
                    if value is not None:
                        return value
            for value in obj.values():
                found = cls._find_value(value, keys)
                if found is not None:
                    return found
        elif isinstance(obj, list):
            for value in obj:
                found = cls._find_value(value, keys)
                if found is not None:
                    return found
        return None

    @staticmethod
    def _player_list(data):
        if isinstance(data, list):
            return data
        if not isinstance(data, dict):
            return []
        # Prima prova i nomi più comuni, poi qualunque lista di dict.
        for key in ("results", "players", "items", "data"):
            value = data.get(key)
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return value
            if isinstance(value, dict):
                nested = MarketClient._player_list(value)
                if nested:
                    return nested
        for value in data.values():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return value
        return []

    def get_cards(self, ids=None, platform="ps"):
        params = {
            "hours": "6",
            "page": 1,
            "onlySpecialCards": "true",
            "price__gte": 300000,
            "price__lte": 3000000,
        }
        r = self.session.get(self.FUTGG_URL, params=params, timeout=30)
        print("FUT.GG HTTP:", r.status_code)
        r.raise_for_status()
        raw_players = self._player_list(r.json())
        print("Carte Momentum ricevute:", len(raw_players))

        cards = []
        for p in raw_players:
            player_id = self._find_value(p, ["id", "player_id", "playerId", "ea_id", "eaId"])
            name = self._find_value(p, ["name", "display_name", "displayName", "common_name", "commonName"])
            price = self._num(self._find_value(p, [
                "price", "price_ps", "pricePs", "current_price", "currentPrice",
                "market_price", "marketPrice", "lowest_price", "lowestPrice"
            ]))
            change = self._num(self._find_value(p, [
                "price_change_percent", "priceChangePercent", "change_percent", "changePercent",
                "percentage_change", "percentageChange", "percent_change", "percentChange",
                "price_change", "priceChange", "momentum"
            ]))

            # Alcune API esprimono -5% come -0.05.
            if change is not None and -1 < change < 1 and change != 0:
                change *= 100

            if player_id is None or price is None or change is None:
                continue
            if not (300000 <= price <= 3000000):
                continue

            cards.append({
                "id": str(player_id),
                "name": str(name or f"Player {player_id}"),
                "market_price": int(price),
                "change_6h": float(change),
            })

        print("Carte con prezzo + variazione 6h leggibili:", len(cards))
        return cards
