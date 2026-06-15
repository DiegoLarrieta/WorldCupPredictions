"""Rebuild intl_possession_raw.csv from the tournaments already CACHED locally
(no new scraping → no laptop heat). Adds AFCON / Nations League / Gold Cup to the
World Cup + Euro data, giving more recent + more non-European possession.
"""
import feature_importance as F

# Only tournaments whose HTML is already cached (season codes match the cache).
F.TOURNAMENTS = [
    ("INT-World Cup", ["2018", "2022"]),
    ("INT-European Championship", ["2020", "2024"]),
    ("INT-AFCON", ["2019", "2020", "2023"]),
    ("INT-Gold Cup", ["2019", "2020", "2023", "2025"]),
    ("INT-Nations League", ["2021", "2223", "2425"]),
]
df = F.pull_team_logs()
print(f"\nWrote intl_possession_raw.csv: {len(df)} rows, "
      f"{df['date'].min().date()} → {df['date'].max().date()}, "
      f"{df['team'].nunique()} teams")
