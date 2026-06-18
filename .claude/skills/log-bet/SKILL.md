---
name: log-bet
description: Record a real or paper bet in the ledger, settle a finished one, or show betting performance (ROI, CLOV). Use when the user says they placed a bet, wants to log/track a wager, settle a result, or see how their bets are doing (e.g. "log a bet on Norway under 2.5 at 1.78", "settle bet 3, it won", "how are my bets doing").
---

# /log-bet

Maintain the bet ledger at `data/bets.csv` — the proprietary closing-line-value (CLOV)
dataset that proves (or disproves) edge over the tournament. Wraps `engine.betlog`.

Three actions: **log** a new bet, **settle** a finished one, **summary** of performance.

## Log a new bet
Gather: match, market (`1x2` / `ou_2.5` / `btts`), selection, the **odds you took**, the
**model probability** (from `prediction.json` / `market_compare.json` for that pick), the
**stake**, and the **book**. If model_prob isn't given, read it from the match's
`market_compare.json` or `prediction.json`.

```bash
.venv/bin/python -c "
from engine.betlog import log_bet
print(log_bet('Iraq vs Norway', 'ou_2.5', 'under', odds_taken=1.78,
              model_prob=0.62, stake=10, book='pinnacle'))
"
```
Confirm the bet_id back to the user — they'll need it to settle.

## Settle a finished bet
Gather: bet_id, result (`win` / `loss` / `void`), and the **closing odds** if known
(enables CLOV — the key metric). 

```bash
.venv/bin/python -c "from engine.betlog import settle; print(settle(3, result='win', closing_odds=1.70))"
```

Encourage capturing closing_odds: CLOV (did we beat the close) is the best leading
indicator of edge, more so than short-run P/L.

## Show performance
```bash
.venv/bin/python -c "from engine.betlog import summary; print(summary())"
```
Report: bets/open/settled, staked, P/L, ROI, hit rate, **avg CLOV + beat-close rate**.
Frame honestly — over a small sample, CLOV is more trustworthy than ROI (variance is
huge). A positive beat-close rate on a losing-money week is still a good sign.

## Reminders
- `data/bets.csv` is committed (money records belong in git). After logging/settling,
  remind the user the ledger changed; offer to commit it.
- This is the live-capture half of the redirect plan: every logged bet, especially in
  markets we have no historical odds for (player props), builds data we can't buy later.
