#!/usr/bin/env python3
"""Build the dashboard's data feed: one self-contained JSON the static frontend reads.

The split (agreed with Diego): the *engine* runs here in the Claude Code session
(predict + odds + analyze + log bets), writing daily_board.json + data/bets.csv. This
script rolls those local files into `dashboard/data.json` — **no API key, no LLM, no
network** — so the dashboard is pure presentation: open it, read the JSON, paint it.

Produces:
  - metrics: bank / #bets / pnl / in-play, off the 10,000 MXN bankroll + the ledger.
  - fixtures: every match on the board (newest first) with flags, the model's market
    probabilities, the market price, the prop recommendations + stakes, and the result.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "data" / "csv" / "derived" / "daily_board.json"
LEDGER = ROOT / "data" / "bets.csv"
OUT = ROOT / "dashboard" / "data.json"
BANKROLL = 10_000          # MXN, the managed starting bank (see memory bankroll-management)

# Country -> flag emoji for every nation that can appear on the board. Unknowns fall back to 🏳.
FLAGS = {
    "Mexico": "🇲🇽", "Czech Republic": "🇨🇿", "South Africa": "🇿🇦", "South Korea": "🇰🇷",
    "Bosnia and Herzegovina": "🇧🇦", "Qatar": "🇶🇦", "Canada": "🇨🇦", "Switzerland": "🇨🇭",
    "Paraguay": "🇵🇾", "Australia": "🇦🇺", "United States": "🇺🇸", "Turkey": "🇹🇷",
    "Morocco": "🇲🇦", "Haiti": "🇭🇹", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Brazil": "🇧🇷",
    "Curaçao": "🇨🇼", "Ivory Coast": "🇨🇮", "Ecuador": "🇪🇨", "Germany": "🇩🇪",
    "Japan": "🇯🇵", "Sweden": "🇸🇪", "Tunisia": "🇹🇳", "Netherlands": "🇳🇱",
    "Egypt": "🇪🇬", "Iran": "🇮🇷", "New Zealand": "🇳🇿", "Belgium": "🇧🇪",
    "Cape Verde": "🇨🇻", "Saudi Arabia": "🇸🇦", "Uruguay": "🇺🇾", "Spain": "🇪🇸",
    "Algeria": "🇩🇿", "Austria": "🇦🇹", "Jordan": "🇯🇴", "Argentina": "🇦🇷",
    "Norway": "🇳🇴", "France": "🇫🇷", "Senegal": "🇸🇳", "Iraq": "🇮🇶",
    "Colombia": "🇨🇴", "Portugal": "🇵🇹", "DR Congo": "🇨🇩", "Uzbekistan": "🇺🇿",
    "Croatia": "🇭🇷", "Ghana": "🇬🇭", "Panama": "🇵🇦", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "Mexico ": "🇲🇽",
}


def flag(team: str) -> str:
    return FLAGS.get(team.strip(), "🏳️")


def amer(price) -> str:
    """Decimal odds -> American string, matching the rest of the board. Pass-through if it's
    already a string (the market odds are stored pre-formatted)."""
    if isinstance(price, str):
        return price
    if not price:
        return "—"
    d = float(price)
    return f"+{round((d - 1) * 100)}" if d >= 2.0 else f"{round(-100 / (d - 1))}"


def _metrics() -> dict:
    """Bank / #bets / P&L / in-play from the ledger, on top of the starting bankroll."""
    rows = []
    if LEDGER.exists():
        with LEDGER.open() as f:
            rows = list(csv.DictReader(f))

    def num(r, k):
        try:
            return float(r.get(k) or 0)
        except ValueError:
            return 0.0

    pnl = sum(num(r, "pnl") for r in rows if (r.get("status") or "").lower() == "settled")
    in_play = sum(num(r, "stake") for r in rows if (r.get("status") or "").lower() == "open")
    settled = [r for r in rows if (r.get("status") or "").lower() == "settled"]
    wins = sum(1 for r in settled if (r.get("result") or "").lower() == "win")
    return {
        "bank": round(BANKROLL + pnl),
        "bankroll_start": BANKROLL,
        "n_bets": len(rows),
        "n_open": sum(1 for r in rows if (r.get("status") or "").lower() == "open"),
        "n_settled": len(settled),
        "pnl": round(pnl),
        "in_play": round(in_play),
        "hit_rate": (round(100 * wins / len(settled)) if settled else None),
        "currency": "MXN",
    }


_RESULT_RE = re.compile(r"\*\*(.+?)\*\*\s*\((\w+)\).*?checks\s+\*\*(\d+/\d+)\*\*")


def _fixture(row: dict) -> dict:
    home, away = row["match"].split(" vs ")
    res = row.get("result") or ""
    score = played = checks = None
    m = _RESULT_RE.search(res)
    if m:
        score, _outcome, checks = m.group(1), m.group(2), m.group(3)
        played = True
    markets = [{"label": lab, "model": round(pr * 100), "odds": od,
                "hit": (hp if len(mk) > 3 else None)}
               for mk in row.get("markets", [])
               for lab, pr, od, *rest in [mk] for hp in [rest[0] if rest else None]]
    recs = [{"player": p["player"], "market": p.get("market", ""), "line": p["line"],
             "odds": amer(p.get("price")),
             "model": round(p.get("model", 0) * 100), "stake": p["stake"]}
            for p in (row.get("prop_recs") or [])]
    return {
        "match": row["match"], "home": home, "away": away,
        "home_flag": flag(home), "away_flag": flag(away),
        "kickoff": row.get("kickoff", ""), "date": row.get("date", ""),
        "played": bool(played), "score": score, "checks": checks,
        "sug": row.get("sug", ""), "markets": markets, "prop_recs": recs,
        "link": row.get("link", ""),
    }


def main() -> None:
    board = json.loads(BOARD.read_text()) if BOARD.exists() else []
    fixtures = [_fixture(r) for r in board if r.get("markets") is not None]
    fixtures.sort(key=lambda f: f.get("kickoff", ""), reverse=True)   # newest first
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"metrics": _metrics(), "fixtures": fixtures},
                              indent=1, ensure_ascii=False))
    print(f"-> {OUT}  ({len(fixtures)} fixtures, bank {_metrics()['bank']:,} MXN)")


if __name__ == "__main__":
    main()
