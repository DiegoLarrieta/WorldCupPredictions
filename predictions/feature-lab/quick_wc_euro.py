"""Fast directional run: WC + Euro only (already cached → no new scraping).
Gives an immediate read on national-possession importance while the full
multi-tournament scrape finishes in the background.
"""
import feature_importance as F

F.TOURNAMENTS = [
    ("INT-World Cup", ["2018", "2022"]),
    ("INT-European Championship", ["2020", "2024"]),
]
F.main()
