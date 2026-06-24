---
name: bet-report
description: The profitability scorecard — are we actually winning? Rolls up the bet ledger (CLOV, ROI with a confidence interval, beat-close rate) plus model calibration. Use when the user asks "are we profitable", "how are the bets doing", "show the scorecard", "what's our CLOV/ROI".
---

# /bet-report

The honest "are we winning?" dashboard. Wraps `engine.betlog.report` (ledger) and the
tournament monitor (calibration). Read `design/profitability-scorecard.md` — this skill
reports against that bar.

## The bar (state it every time)
Profitable is **NOT** accuracy or P/L on a good week. Two metrics, in order:
1. **CLOV — the leading indicator.** Did we take prices better than the sharp close?
   `avg_clov > 0` and `beat_close_rate` high = edge signal, *even on a losing week*. Trust
   this over ROI at small samples (ROI variance is huge).
2. **ROI with a confidence interval — the verdict.** Profitable = the **ROI CI lower bound
   is above 0** (`roi_profitable`). If the CI crosses 0, we do **not** know yet — that's
   "no evidence", not "almost".

## Steps
```bash
.venv/bin/python -c "
from engine.betlog import report
import json; print(json.dumps(report(), indent=1))
"
# calibration side (how honest were the predictions):
#   read data/worldcupmatches/_monitor.md (ensemble RPS vs uniform, ECE)
```

## Reporting
- Lead with **CLOV**: `avg_clov` (+CI) and `beat_close_rate`. This is the headline at any n.
- Then **ROI + CI** and the verdict: `roi_profitable` true → CI above 0, real evidence;
  false → inconclusive (say how many more bets we'd want, ~30-50 of a type).
- Split honestly by market if asked (props vs 1X2): props are the edge target; 1X2 is
  record-only (edge test). A losing-money week with positive CLOV is a **good** sign — say so.
- Add the calibration line from the monitor (are our 70%s really ~70%?) — that's the
  prediction-quality half, separate from bet selection.

## Reminders
- Empty/small ledger is normal early — report it plainly (CIs will be `[None, None]` or very
  wide). Don't over-interpret a handful of bets.
- CLOV needs the **closing** price captured: ensure odds snapshots ran to kickoff and bets
  were settled with `closing_odds` (via /log-bet) — otherwise `avg_clov` is blank and we're
  flying blind, which is itself the thing to flag.
- This is read-only: it judges, it doesn't place or settle bets (use /log-bet for that).
