-- The Assignment, in SQL: turn closing 1X2 odds into the market's vig-removed
-- implied probability for every match, then sit it next to the actual result.
-- This is the harness every future model must beat. Defines two views:
--   market_prob      de-vigged probability per match/book/outcome
--   match_vs_market  one row per match: market prob vs actual result

-- Raw implied prob = 1 / decimal_odds. These sum to >1 because of the bookmaker
-- margin (the "vig"). We normalize each match's three selections to sum to 1 to
-- recover the market's true probability estimate (basic multiplicative de-vig).
CREATE OR REPLACE VIEW market_prob AS
WITH raw AS (
    SELECT
        match_id,
        bookmaker,
        selection,
        1.0 / price AS raw_prob
    FROM match_odds
    WHERE market = '1x2'
),
overround AS (
    SELECT match_id, bookmaker, SUM(raw_prob) AS book_sum
    FROM raw
    GROUP BY match_id, bookmaker
)
SELECT
    r.match_id,
    r.bookmaker,
    r.selection,
    r.raw_prob / o.book_sum            AS implied_prob,  -- de-vigged
    o.book_sum - 1.0                   AS vig            -- bookmaker margin
FROM raw r
JOIN overround o USING (match_id, bookmaker);

-- One row per match: market's de-vigged probabilities (Bet365) vs the actual
-- result. This is what you eyeball first, and what a model's prob plugs into later.
CREATE OR REPLACE VIEW match_vs_market AS
SELECT
    m.match_id,
    m.date,
    m.home_team,
    m.away_team,
    CASE                                       -- H / D / A (actual), derived from goals
        WHEN m.home_goals > m.away_goals THEN 'H'
        WHEN m.home_goals = m.away_goals THEN 'D'
        ELSE 'A'
    END AS result,
    MAX(CASE WHEN p.selection = 'home' THEN p.implied_prob END) AS p_home,
    MAX(CASE WHEN p.selection = 'draw' THEN p.implied_prob END) AS p_draw,
    MAX(CASE WHEN p.selection = 'away' THEN p.implied_prob END) AS p_away,
    MAX(p.vig)                                                  AS vig
FROM matches m
JOIN market_prob p
  ON p.match_id = m.match_id AND p.bookmaker = 'bet365'
GROUP BY 1, 2, 3, 4, 5
ORDER BY m.date;
