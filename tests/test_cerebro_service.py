from pathlib import Path

from src.schemas.cerebro import CerebroKeywordRow
from src.services import cerebro_service

SAMPLE_FILE = Path(__file__).parent / "fixtures" / "cerebro_sample.csv"


def _make_row(**overrides) -> CerebroKeywordRow:
    defaults = dict(
        keyword="keyword",
        search_volume=100,
        search_volume_trend=0,
        suggested_bid=1.0,
        competing_products=10,
        title_density=1,
        is_organic=True,
        is_sponsored=True,
        position_rank=5,
        competitor_ranks={},
    )
    defaults.update(overrides)
    return CerebroKeywordRow(**defaults)


def test_ingest_returns_all_rows_from_sample():
    rows = cerebro_service.ingest(SAMPLE_FILE.read_bytes())

    assert len(rows) == 2


def test_find_keyword_is_case_insensitive():
    rows = [_make_row(keyword="Wine Saver")]

    assert cerebro_service.find_keyword(rows, "wine saver") is not None
    assert cerebro_service.find_keyword(rows, "WINE SAVER") is not None


def test_find_keyword_returns_none_when_absent():
    rows = [_make_row(keyword="wine saver")]

    assert cerebro_service.find_keyword(rows, "nonexistent keyword") is None


def test_opportunity_keywords_excludes_already_targeted_and_sorts_by_volume():
    rows = [
        _make_row(keyword="already targeted", search_volume=5000),
        _make_row(keyword="big opportunity", search_volume=2000),
        _make_row(keyword="small opportunity", search_volume=100),
    ]

    opportunities = cerebro_service.opportunity_keywords(rows, targeted_keywords={"already targeted"})

    assert [row.keyword for row in opportunities] == ["big opportunity", "small opportunity"]


def test_opportunity_keywords_matching_is_case_insensitive():
    rows = [_make_row(keyword="Wine Saver", search_volume=100)]

    opportunities = cerebro_service.opportunity_keywords(rows, targeted_keywords={"wine saver"})

    assert opportunities == []


def test_opportunity_keywords_respects_limit():
    rows = [_make_row(keyword=f"kw{i}", search_volume=i) for i in range(20)]

    opportunities = cerebro_service.opportunity_keywords(rows, targeted_keywords=set(), limit=5)

    assert len(opportunities) == 5
    assert opportunities[0].keyword == "kw19"  # highest search volume first


def test_estimate_page_rounds_up():
    assert cerebro_service.estimate_page(1) == 1
    assert cerebro_service.estimate_page(24) == 1
    assert cerebro_service.estimate_page(25) == 2
    assert cerebro_service.estimate_page(48) == 2
    assert cerebro_service.estimate_page(49) == 3
