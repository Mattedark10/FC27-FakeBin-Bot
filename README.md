# FC27 Momentum Alert — GitHub Actions

Monitor FUT.GG Momentum 6h, pagina 1, solo carte speciali tra 300.000 e 3.000.000 coin.
Invia un alert Telegram quando FUT.GG indica una variazione 6h di almeno -5%.

## GitHub Secrets
Crea soltanto:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Non usa Parse e non richiede `MARKET_API_KEY`.

## Workflow
`.github/workflows/fc27-monitor.yml` parte manualmente oppure ogni 5 minuti. `state.json` viene salvato nel repository per evitare alert identici ad ogni esecuzione.
