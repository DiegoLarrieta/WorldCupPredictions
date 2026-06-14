PY := .venv/bin/python
SRC := src/phase0

# Full pipeline, in dependency order. DuckDB is the source of truth;
# `export` writes the human-browsable CSV mirror under data/csv/.
.PHONY: data
data: spine players nationality fbref squads bridge backtest export

spine:        ; $(PY) $(SRC)/ingest.py            # matches, team_ratings, teams, match_odds
players:      ; $(PY) $(SRC)/ingest_players.py    # clubs, players, player_seasons (Understat big-5)
nationality:  ; $(PY) $(SRC)/ingest_nationality.py # players.nationality + born (FBref)
fbref:        ; $(PY) $(SRC)/ingest_fbref_leagues.py # +Liga MX/MLS/Brazil/Saudi (goals only, no xG)
squads:       ; $(PY) $(SRC)/ingest_squads.py     # wc_squads (Wikipedia convocados)
bridge:       ; $(PY) $(SRC)/bridge_squad_form.py # wc_squad_form, wc_team_strength
backtest:     ; cd $(SRC) && ../../$(PY) backtest_elo.py  # derived/elo_calibration.csv
export:       ; $(PY) $(SRC)/export_csv.py        # all tables/views -> data/csv/<folder>/
