from pathlib import Path

import pytest

from src.repositories import cerebro_repository

SAMPLE_FILE = Path(__file__).parent / "fixtures" / "cerebro_sample.csv"


def _parse_sample():
    return cerebro_repository.parse(SAMPLE_FILE.read_bytes())


def test_parse_returns_all_keyword_rows():
    rows = _parse_sample()

    assert len(rows) == 2


def test_parse_detects_competitor_asin_columns_dynamically():
    rows = _parse_sample()
    row = next(r for r in rows if r.keyword == "vacu vin wine saver pump")

    assert set(row.competitor_ranks) == {
        "B07ZTXD1R6",
        "B004O0TJFY",
        "B09K7Q6S7V",
        "B0D9VC26D5",
        "B00005U2FA",
        "B08YY8PGVJ",
    }


def test_parse_reads_known_row_values():
    rows = _parse_sample()
    row = next(r for r in rows if r.keyword == "vacu vin wine saver pump")

    assert row.search_volume == 544
    assert row.position_rank == 11
    assert row.competitor_ranks["B07ZTXD1R6"] == 9
    assert row.competitor_ranks["B09K7Q6S7V"] == 45


def test_parse_treats_dash_and_blank_as_missing_value():
    rows = _parse_sample()
    row = next(r for r in rows if r.keyword == "vin saver")

    # "vin saver" has a blank suggested bid and doesn't rank for B09K7Q6S7V ("-").
    assert row.suggested_bid is None
    assert row.competitor_ranks["B09K7Q6S7V"] is None
    assert row.competitor_ranks["B0D9VC26D5"] == 2


def test_parse_rejects_file_missing_required_columns():
    wrong_file = b"Targeting,Target bid\nwine saver,0.65\n"

    with pytest.raises(ValueError, match="doesn't look like a Helium 10 Cerebro export"):
        cerebro_repository.parse(wrong_file)
