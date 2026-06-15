# Data Model — World Cup Match Predictor

The whole design hangs on one idea: **the player is the bridge between the club world
(where form is measured) and the country world (what we predict).** Everything below
exists to make this query possible:

> "France play Croatia. Who's in France's lineup? What club is each player at? How is
>  he doing there *right now*? Aggregate that into France's strength today."

## Current schema (renamed 2026-06-14 — authoritative)

Plain names, grouped into CSV folders under `data/csv/`. The ERD below uses the original
concept names; this table is the source of truth for what exists today.

| table | folder | one row per | key columns |
|---|---|---|---|
| `teams` | reference | national team | team_name (PK), canonical_name |
| `team_ratings` | reference | national team | team_name, elo |
| `clubs` | reference | club | club_id (PK), name, league |
| `players` | reference | player (PIVOT) | player_id (PK), name, position, current_club_id→clubs, nationality, born |
| `matches` | matches | match | match_id (PK), date, home_team, away_team, goals, is_international |
| `match_odds` | matches | match·book·outcome | match_id→matches, bookmaker, market, selection, price |
| `player_seasons` | form | player·season·club | player_id→players, season, club_id→clubs, minutes, goals, xg, np_xg, xa |
| `wc_squads` | worldcup | squad player | **squad_player_id (PK)**, country, shirt_no, position, player, dob, caps, intl_goals, club |
| `wc_squad_form` | worldcup | squad player | squad_player_id (PK) + player_id→players (NULL if no club form) + club form + has_club_form |
| `wc_team_strength` | worldcup | country | country, squad_size, with_form, avg_npxg_per90, total_caps, team_elo |
| `market_prob` *(view)* | derived | match·book·outcome | de-vigged implied probability |
| `match_vs_market` *(view)* | derived | match | market prob vs actual result |
| `elo_calibration` *(report)* | derived | prediction bin | predicted vs actual (backtest output) |

Dropped (2026-06-14): `fact_match_team_stats` — EPL-only team xG, unused in the prediction
path, with a spurious `game_id`/`match_id` collision. The player-level `player_seasons`
carries the form signal we actually use.

Naming rule: **"team" always means a national team; "club" always means a club side.**

## Entity-Relationship diagram

```
        COUNTRY WORLD                              CLUB WORLD
  ┌───────────────────────┐                 ┌───────────────────────┐
  │ dim_team              │                 │ dim_club              │
  │ • team (PK)           │                 │ • club_id (PK)        │
  │ • iso_code            │                 │ • name (Real Madrid)  │
  │ • confederation       │                 │ • league (ESP-La Liga)│
  └──────────┬────────────┘                 └───────────┬───────────┘
             │ has many                                  │ employs
             │                                           │
             │         ┌───────────────────────┐         │
             │         │ dim_player   (PIVOT)   │         │
             └────────▶│ • player_id (PK)       │◀────────┘
        nationality    │ • name (Kylian Mbappé) │   current_club_id
                       │ • nationality → dim_team│
                       │ • current_club_id ─────→ dim_club
                       └───────┬───────────┬─────┘
                  appears in   │           │  accumulates
                               ▼           ▼
        ┌──────────────────────────┐   ┌────────────────────────────────┐
        │ fact_lineup              │   │ fact_player_season             │
        │ • match_id → fact_match  │   │ • player_id → dim_player       │
        │ • team (country)         │   │ • season  (2425)               │
        │ • player_id → dim_player │   │ • club_id → dim_club           │
        │ • is_starter, minutes    │   │ • minutes, goals, assists      │
        │   (WHO plays a national  │   │ • xg, npxg, xa  (FORM signal)  │
        │    match)                │   │   (one row per player·season)  │
        └────────────┬─────────────┘   └────────────────────────────────┘
                     │ belongs to
                     ▼
  ┌───────────────────────────────────────────────────────────────────┐
  │ fact_match   — every match (internationals + club)                 │
  │ • match_id (PK) • date • home_team • away_team • goals • result     │
  │ • is_international • tournament • neutral                           │
  └──────────────┬───────────────────────────┬────────────────────────┘
                 │ priced by                  │ described by
                 ▼                            ▼
  ┌──────────────────────────┐   ┌────────────────────────────────────┐
  │ fact_odds (long)         │   │ fact_match_team_stats              │
  │ • match_id • bookmaker   │   │ • game_id • team_id • is_home      │
  │ • market • selection     │   │ • xg • npxg • ppda • deep          │
  │ • price • captured_at    │   │ • shots • shots_on_target          │
  └──────────────────────────┘   └────────────────────────────────────┘

  team_elo (team → elo)  — recency-aware national-team strength, keyed to dim_team
```

## Tables, by status

### Already built (Phase 0 + Step 2)
| table | grain (one row per…) | key columns | source |
|---|---|---|---|
| `fact_match` | match | match_id, date, home_team, away_team, goals, is_international | martj42 + football-data |
| `team_elo` | national team | team, elo | computed |
| `dim_team` | national team | team, canonical | martj42 |
| `fact_odds` | match·book·outcome | match_id, bookmaker, market, selection, price | football-data |
| `fact_match_team_stats` | club match·team | game_id, team_id, xg, npxg, ppda, shots, shots_on_target | Understat |

### The player layer — building NOW
| table | grain | key columns | source |
|---|---|---|---|
| `dim_club` | club | club_id (PK), name, league | Understat |
| `dim_player` | player | player_id (PK), name, nationality→dim_team, current_club_id→dim_club | Understat (+ nationality TBD) |
| `fact_player_season` | player·season | player_id, season, club_id, minutes, goals, assists, xg, npxg, xa | Understat |

### The player layer — needs a new source (next, not now)
| table | grain | key columns | source |
|---|---|---|---|
| `fact_lineup` | national match·player | match_id, team, player_id, is_starter, minutes | **TBD** — national squads/lineups (FBref or a WC squad list) |

## The honest gap (read this)

The club-form half (`dim_player`, `dim_club`, `fact_player_season`) builds cleanly from
Understat **today**. But two links need a source Understat does not provide:

1. **Player → nationality.** Understat is club-only; it does not say Mbappé is French.
   Filling `dim_player.nationality` needs a squad list or FBref player bios.
2. **National lineups** (`fact_lineup`) — who actually starts France vs Croatia. martj42
   has results but no lineups. This needs FBref international match data or a squad source.

Until those land, we have each player's **club form** but not yet the wiring that says
"these 11 form numbers belong to France's lineup." So we build the form layer now, then
solve the nationality/lineup join as its own step (it is the real entity-resolution work:
matching "K. Mbappé" in Understat to "Kylian Mbappé" in a squad list).

## The prediction query (the target this all serves)

```
fact_match (France vs Croatia, international)
   └─ fact_lineup  → France's 11 player_ids        [needs source]
        └─ dim_player → each player's current_club_id
             └─ fact_player_season → his club xg / goals / minutes this season
                  └─ AGGREGATE → France attack-strength, defense-strength (today)
   └─ team_elo (France, Croatia) → baseline strength
   └─ fact_odds → the market line to beat
   = features for the model
```

Engine: **local DuckDB** through the modeling phase. Schema is standard SQL, so a later
move to Postgres/Supabase (only when an app needs hosted data) is near copy-paste.
