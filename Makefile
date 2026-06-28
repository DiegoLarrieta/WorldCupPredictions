PY := .venv/bin/python
SRC := src/phase0

# Full pipeline, in dependency order. DuckDB is the source of truth;
# `export` writes the human-browsable CSV mirror under data/csv/.
.PHONY: data dashboard
data: spine players nationality fbref squads bridge backtest export

# Betting dashboard: rebuild the data feed from the board + ledger, then serve
# the static panel locally (no API key, no LLM — pure presentation of what the
# engine already wrote). Opens http://localhost:8787.
dashboard:    ; $(PY) scripts/build_dashboard.py && echo "→ http://localhost:8787 (Ctrl+C para parar)" && ( sleep 1 && open http://localhost:8787 >/dev/null 2>&1 || true ) & cd dashboard && ../$(PY) -m http.server 8787

spine:        ; $(PY) $(SRC)/ingest.py            # matches, team_ratings, teams, match_odds
players:      ; $(PY) $(SRC)/ingest_players.py    # clubs, players, player_seasons (Understat big-5)
nationality:  ; $(PY) $(SRC)/ingest_nationality.py # players.nationality + born (FBref)
fbref:        ; $(PY) $(SRC)/ingest_fbref_leagues.py # +Liga MX/MLS/Brazil/Saudi (goals only, no xG)
squads:       ; $(PY) $(SRC)/ingest_squads.py     # wc_squads (Wikipedia convocados)
bridge:       ; $(PY) $(SRC)/bridge_squad_form.py # wc_squad_form, wc_team_strength
backtest:     ; cd $(SRC) && ../../$(PY) backtest_elo.py  # derived/elo_calibration.csv
export:       ; $(PY) $(SRC)/export_csv.py        # all tables/views -> data/csv/<folder>/
