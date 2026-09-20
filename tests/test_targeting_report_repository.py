from pathlib import Path

import pytest

from src.repositories import targeting_report_repository

SAMPLE_FILE = Path(__file__).parent / "fixtures" / "targeting_report_sample.csv"


def _parse_sample():
    return targeting_report_repository.parse(SAMPLE_FILE.read_bytes())


def test_parse_skips_ad_group_subtotal_rows():
    rows = _parse_sample()

    # The fixture has 4 data rows, 1 of which is an ad-group subtotal row
    # with a blank "Targeting" value rather than a real keyword target.
    assert len(rows) == 3
    assert all(row.keyword for row in rows)


def test_parse_unescapes_excel_formula_wrapped_ids():
    rows = _parse_sample()
    row = next(r for r in rows if r.keyword == "wine saver" and r.match_type == "PHRASE")

    assert row.campaign_id == "126573957133472"
    assert row.ad_group_id == "404177307017804"


def test_parse_reads_known_row_values():
    rows = _parse_sample()
    row = next(r for r in rows if r.keyword == "wine saver" and r.match_type == "PHRASE")

    assert row.campaign_name == "DEMO | SP | MANUAL | CORE"
    assert row.ad_group_name == "DEMO CORE KEYWORDS"
    assert row.bid == 0.65
    assert row.status == "ENABLED"
    assert row.impressions == 18
    assert row.clicks == 1
    assert row.cost == 0.65
    assert row.sales == 0.0
    assert row.purchases == 0
    assert row.units_sold == 0


def test_parse_distinguishes_same_keyword_by_match_type():
    rows = _parse_sample()
    wine_saver_rows = [r for r in rows if r.keyword == "wine saver"]

    assert {r.match_type for r in wine_saver_rows} == {"PHRASE", "EXACT"}


def test_parse_rejects_file_missing_required_columns():
    wrong_file = b"Keyword Phrase,Search Volume\nvin saver,315\n"

    with pytest.raises(ValueError, match="doesn't look like a Sponsored Products Targeting"):
        targeting_report_repository.parse(wrong_file)


def test_parse_falls_back_to_cp1252_when_not_valid_utf8():
    header = ",".join(f'"{c}"' for c in targeting_report_repository.REQUIRED_COLUMNS)
    # "café" saved as Windows-1252 (Excel default), not valid UTF-8.
    row = (
        '"1","café brand","1","ag","wine café","EXACT","1","0.5",'
        '"ENABLED","10","1","1.00","0","0.00","0"'
    )
    raw = (header + "\n" + row).encode("cp1252")

    rows = targeting_report_repository.parse(raw)

    assert rows[0].campaign_name == "café brand"
    assert rows[0].keyword == "wine café"


def test_parse_raises_clear_error_for_undecodable_bytes():
    # Undefined in both UTF-8 and Windows-1252 (cp1252).
    with pytest.raises(ValueError, match="Couldn't read this file as text"):
        targeting_report_repository.parse(b"\x81\x8d\x8f\x90\x9d")
