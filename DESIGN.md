# DESIGN.md — WC Betting Desk

Design system for the betting dashboard (`dashboard/`). Built via `/design-consultation`.

## Memorable thing
> "Esto es software serio para apostar dinero serio." A betting trading-desk at night —
> dark, dense, precise. The money is the hero.

## Aesthetic
Bloomberg terminal × sportsbook. Near-black, high-contrast, data-dense but legible. No
decoration that isn't a number or a state. Color is reserved for meaning (money up/down, live).

## Typography
- **Headings / UI:** Space Grotesk (tight grotesk, −0.02em tracking).
- **Numbers / data:** JetBrains Mono. Every figure — money, odds, probabilities, scores — is
  mono so columns align and digits read like a terminal.

## Color tokens
| token | hex | use |
|---|---|---|
| `--bg` | `#0B0E13` | page (radial wash to `#121a2a` top-right) |
| `--surface` / `--surface2` | `#151A22` / `#1C232E` | cards, rows |
| `--line` | `#252D3A` | borders, dividers |
| `--text` / `--muted` / `--muted2` | `#E6EAF0` / `#7A8699` / `#566072` | text hierarchy |
| `--green` | `#2ED47A` | profit, won checks, stakes |
| `--red` | `#FF5C5C` | loss, failed checks |
| `--amber` | `#F5A623` | live / in-play / upcoming |
| `--blue` | `#3B82F6` | primary actions ("Predecir partido"), model probabilities |

Rule: green = money/edge in our favor, red = against, amber = live/at-risk, blue = action + model.

## Layout
- **Topbar:** brand + bank badge (always-visible current bankroll).
- **Metrics row:** 4 cards (Banca · Apuestas · Ganancias · En juego), big mono numbers, a 3px
  top accent bar colored by meaning (P&L card flips green/red).
- **Board:** fixtures grouped by date (newest first); each row = flags + teams + kickoff +
  status (score/checks or "Por jugarse") + a `Predecir partido` / `Ver predicción` button.
  Click expands a dense markets table (model% vs the price, with ✓/✗ checks) + a green
  "Props recomendados" block with MXN stakes.

## Architecture note (not just visual)
The dashboard is **pure presentation**: it reads `dashboard/data.json` (built by
`scripts/build_dashboard.py` from `daily_board.json` + `data/bets.csv`). No API key, no LLM,
no backend. The engine runs in the Claude Code session and writes the data; the panel paints
it. Run with `make dashboard` → http://localhost:8787.
