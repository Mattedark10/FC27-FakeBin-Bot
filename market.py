import requests
from datetime import datetime, timezone, timedelta


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
        # FUT.GG MOMENTUM
        # 6H - PAGINA 1 - SOLO SPECIALI
        # PREZZO 300K - 3M
        # ==========================================

        futgg_url = (
            "https://www.fut.gg/api/fut/players/v2/27/"
        )

        params = {
            "hours": '"6"',
            "page": 1,
            "price__gte": 300000,
            "price__lte": 3000000,
            "onlySpecialCards": "true"
        }

        try:
            r = self.session.get(
                futgg_url,
                params=params,
                headers={
                    "Referer": (
                        "https://www.fut.gg/players/momentum/"
                        "?hours=%226%22"
                        "&page=1"
                        "&price__gte=300000"
                        "&price__lte=3000000"
                        "&onlySpecialCards=true"
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
            "Carte Momentum SPECIAL ricevute:",
            self.total_momentum
        )

        alerts = []

        print()
        print("========== CONTROLLO SPECIAL 6H ==========")

        # ==========================================
        # PREZZO + STORICO PER OGNI CARTA
        # ==========================================

        for number, player in enumerate(players, 1):

            name = (
                player.get("commonName")
                or player.get("cardName")
                or "Unknown"
            )

            ea_id = player.get("eaId")

            rarity = (
                player.get("rarityName")
                or "Special"
            )

            overall = player.get("overall")

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

            # ==========================================
            # CREA COPPIE TIMESTAMP + PREZZO
            # ==========================================

            samples = []

            for timestamp, price in zip(
                timestamps,
                prices
            ):
                if not timestamp or not price:
                    continue

                try:
                    # Timestamp numerico Unix
                    if isinstance(
                        timestamp,
                        (int, float)
                    ):
                        dt = datetime.fromtimestamp(
                            timestamp,
                            tz=timezone.utc
                        )

                    # Timestamp ISO
                    else:
                        dt = datetime.fromisoformat(
                            str(timestamp).replace(
                                "Z",
                                "+00:00"
                            )
                        )

                        if dt.tzinfo is None:
                            dt = dt.replace(
                                tzinfo=timezone.utc
                            )

                    samples.append(
                        (dt, int(price))
                    )

                except Exception:
                    continue

            if not samples:
                continue

            samples.sort(
                key=lambda x: x[0]
            )

            current_time, current_price = (
                samples[-1]
            )

            self.with_price += 1

            # ==========================================
            # CERCA IL PREZZO PIÙ VICINO A 6H FA
            # ==========================================

            target_time = (
                current_time
                - timedelta(hours=6)
            )

            old_samples = [
                sample
                for sample in samples
                if sample[0] <= current_time
            ]

            if not old_samples:
                continue

            closest = min(
                old_samples,
                key=lambda sample: abs(
                    (
                        sample[0]
                        - target_time
                    ).total_seconds()
                )
            )

            old_time, price_6h = closest

            distance = abs(
                (
                    old_time
                    - target_time
                ).total_seconds()
            )

            # Il punto deve essere abbastanza vicino
            # alle 6 ore.
            # Accettiamo massimo 45 minuti di differenza.

            if distance > 45 * 60:

                print(
                    f"{number}. {name} | "
                    f"{current_price:,} | "
                    f"{rarity} | "
                    f"storico insufficiente"
                )

                continue

            self.with_6h_history += 1

            # ==========================================
            # CALCOLO VARIAZIONE
            # ==========================================

            change = (
                (current_price - price_6h)
                / price_6h
                * 100
            )

            print(
                f"{number}. {name} | "
                f"{rarity} | "
                f"Now: {current_price:,} | "
                f"6H: {price_6h:,} | "
                f"{change:+.2f}%"
            )

            # ==========================================
            # PREZZO 300K - 3M
            # ==========================================

            if current_price < 300000:
                continue

            if current_price > 3000000:
                continue

            # ==========================================
            # DEVE ESSERE SCESA ALMENO DEL 5%
            # ==========================================

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
                "overall": overall,
                "rarity": rarity,

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

        print()
        print("===================================")
        print("RISULTATO SPECIAL MOMENTUM")
        print("===================================")

        print(
            "Carte special controllate:",
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

        print("===================================")

        return alerts