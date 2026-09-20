import re

# Columns present in every Helium 10 Cerebro export, regardless of which
# competitor ASINs were tracked for that particular report.
CEREBRO_FIXED_COLUMNS = {
    "Keyword Phrase",
    "ABA Total Click Share",
    "ABA Total Conv. Share",
    "Keyword Sales",
    "Cerebro IQ Score",
    "Search Volume",
    "Search Volume Trend",
    "H10 PPC Sugg. Bid",
    "H10 PPC Sugg. Min Bid",
    "H10 PPC Sugg. Max Bid",
    "Sponsored ASINs",
    "Competing Products",
    "CPR",
    "Title Density",
    "Amazon Recommended",
    "Sponsored",
    "Organic",
    "Sponsored Rank (avg)",
    "Sponsored Rank (count)",
    "Amazon Recommended Rank (avg)",
    "Amazon Recommended Rank (count)",
    "Position (Rank)",
    "Relative Rank",
    "Competitor Rank (avg)",
    "Ranking Competitors (count)",
    "Competitor Performance Score",
}

# Any header not in the fixed set is a tracked competitor ASIN column; this
# pattern is just a sanity check that it actually looks like one.
ASIN_PATTERN = re.compile(r"^[A-Z0-9]{10}$")

# Amazon's search results page mixes organic listings with sponsored/featured
# slots, and the exact count varies by layout and personalization — this is a
# rough midpoint used only to turn a rank number into an approximate page,
# never an exact guarantee.
ESTIMATED_RESULTS_PER_PAGE = 24

# Friendly labels for the competitor ASINs already identified for this
# product's Cerebro export. Falls back to the raw ASIN for anything not
# listed here (e.g. a future Cerebro export tracking different competitors).
KNOWN_COMPETITOR_NAMES: dict[str, str] = {
    "B00005U2FA": "Vacu Vin Wine Saver Concerto (4 stoppers)",
    "B08YY8PGVJ": "Vacu Vin Wine Saver Concerto (2 stoppers)",
    "B07ZTXD1R6": "Vacu Vin Original Saver (4 stoppers)",
    "B004O0TJFY": "Vacu Vin Original Saver (1 stopper)",
    "B0D9VC26D5": "WOTOR Wine Saver Vacuum Pump (20 stoppers)",
    "B09K7Q6S7V": "OWO Wine Vacuum Pump (stainless steel)",
}
