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

    def is_special(self, player):
        rarity = str(
            player.get("rarityName") or ""
        ).strip().lower()

        # Carte base normali da escludere
        NON_SPECIAL = {
            "rare",
            "common",
        }

        return rarity not in NON_SPECIAL and rarity != ""

    def get_momentum_specials(self):
        url = "https://www.fut.gg/api/fut/players/v2/27/"

        specials = []
        seen = set()

        # Leggiamo più pagine perché l'API ignora
        # onlySpecialCards.
        for page in range(1, 6):

            params = {
                "hours": '"6"',
                "page": page,
                "price__gte": 300000,
                "price__lte": 3000000
            }

            try:
                r = self.session.get(
                    url,
                    params=params,
                    headers={
                        "Referer": (
                            "https://www.fut.gg/players/momentum/"
                            "?hours=%226%22"
                            f"&page={page}"
                            "&price__gte=300000"
                            "&price__lte=3000000"
                            "&onlySpecialCards=true"
                        )
                    },
                    timeout=30
                )

                print(
                    f"FUT.GG pagina {page} HTTP:",
                    r.status_code
                )

                r.raise_for_status()

                data = r.json()
                players = data.get("data", [])

            except Exception as e:
                print(
                    f"❌ Errore FUT.GG pagina {page}:",
                    e
                )
                continue

            if not isinstance(players, list):
                continue

            for player in players:

                if not self.is_special(player):
                    continue

                # Usiamo eaId perché due versioni diverse
                # dello stesso giocatore devono restare separate.
                ea_id = player.get("eaId")

                if not ea_id:
                    continue

                if ea_id in seen:
                    continue

                seen.add(ea_id)
                specials.append(player)

                if len(specials) >= 30:
                    break

            print(
                f"Special trovate finora: {len(specials)}"
            )

            if len(specials) >= 30:
                break

        return specials[:30]

    def parse_timestamp(self, timestamp):
        try:
            if isinstance(timestamp, (int, float)):

                # Supporto anche timestamp in millisecondi
                if timestamp > 10_000_000_000:
                    timestamp = timestamp / 1000

                return datetime.fromtimestamp(
                    timestamp,
                    tz=timezone.utc
                )

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

            return dt

        except Exception:
            return None

    def get_cards(self, ids=None, platform="ps"):

        players = self.get_momentum_specials()

        self.total_momentum = len(players)

        print()
        print(
            "Carte Momentum SPECIAL ricevute:",
            self.total_momentum
        )

        alerts = []

        print()
        print(
            "========== CONTROLLO SPECIAL 6H =========="
        )

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
                        f"{rarity} | "
                        f"History HTTP {h.status_code}"
                    )
                    continue

                history = h.json()

            except Exception as e:
                print(
                    f"{number}. {name} | "
                    f"{rarity} | "
                    f"Errore history: {e}"
                )
                continue

            timestamps = history.get("t", [])
            prices = history.get("p", [])

            samples = []

            for timestamp, price in zip(
                timestamps,
                prices
            ):
                if timestamp is None:
                    continue

                if not price:
                    continue

                dt = self.parse_timestamp(timestamp)

                if dt is None:
                    continue

                try:
                    price = int(price)
                except Exception:
                    continue

                samples.append(
                    (dt, price)
                )

            if not samples:
                print(
                    f"{number}. {name} | "
                    f"{rarity} | "
                    "nessun prezzo"
                )
                continue

            samples.sort(
                key=lambda x: x[0]
            )

            current_time, current_price = samples[-1]

            self.with_price += 1

            # ==============================
            # CERCA ESATTAMENTE ~6 ORE FA
            # ==============================

            target_time = (
                current_time
                - timedelta(hours=6)
            )

            closest = min(
                samples,
                key=lambda sample: abs(
                    (
                        sample[0] - target_time
                    ).total_seconds()
                )
            )

            old_time, price_6h = closest

            distance_seconds = abs(
                (
                    old_time - target_time
                ).total_seconds()
            )

            # Massimo 45 minuti di distanza
            # dal punto esatto delle 6 ore.
            if distance_seconds > 45 * 60:

                oldest_time = samples[0][0]

                available_hours = (
                    current_time - oldest_time
                ).total_seconds() / 3600

                print(
                    f"{number}. {name} | "
                    f"{current_price:,} | "
                    f"{rarity} | "
                    f"storico {available_hours:.1f}H"
                )

                continue

            self.with_6h_history += 1

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

            # Sicurezza ulteriore sul prezzo
            if current_price < 300000:
                continue

            if current_price > 3000000:
                continue

            # Deve essere scesa almeno del 5%
            if change > -5:
                continue

            path = player.get("url", "")

            if path.startswith("/"):
                player_url = (
                    "https://www.fut.gg" + path
                )
            else:
                player_url = path

            alerts.append({
                "id": player.get("id"),
                "ea_id": ea_id,
                "name": name,
                "overall": overall,
                "rarity": rarity,
                "market_price": current_price,
                "reference_price": price_6h,
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