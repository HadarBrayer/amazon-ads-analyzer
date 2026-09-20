from pathlib import Path

from src.schemas.targeting_report import KeywordPerformance
from src.services import targeting_report_service

SAMPLE_FILE = Path(__file__).parent / "fixtures" / "targeting_report_sample.csv"


def _ingest_sample():
    return targeting_report_service.ingest(SAMPLE_FILE.read_bytes())


def _make_performance(**overrides) -> KeywordPerformance:
    defaults = dict(
        campaign_id="1",
        campaign_name="campaign",
        ad_group_id="1",
        ad_group_name="ad group",
        target_id="1",
        keyword="keyword",
        match_type="EXACT",
        bid=1.0,
        status="ENABLED",
        impressions=0,
        clicks=0,
        cost=0.0,
        sales=0.0,
        purchases=0,
        units_sold=0,
        ctr=None,
        cpc=None,
        acos=None,
        roas=None,
        cvr=None,
        aov=None,
    )
    defaults.update(overrides)
    return KeywordPerformance(**defaults)


def test_ingest_returns_one_performance_row_per_keyword():
    performances = _ingest_sample()

    assert len(performances) == 3


def test_derived_metrics_for_row_with_clicks_but_no_sales():
    performances = _ingest_sample()
    row = next(
        p for p in performances if p.keyword == "wine saver" and p.match_type == "PHRASE"
    )

    # 18 impressions, 1 click, $0.65 cost, $0 sales, 0 purchases
    assert row.ctr == 1 / 18
    assert row.cpc == 0.65
    assert row.cvr == 0.0
    assert row.roas == 0.0
    # Undefined when the denominator is zero, not a fabricated 0.
    assert row.acos is None
    assert row.aov is None


def test_derived_metrics_for_row_with_no_clicks_at_all():
    performances = _ingest_sample()
    row = next(p for p in performances if p.keyword == "wine preservation system")

    # 1 impression, 0 clicks, $0 cost, $0 sales, 0 purchases
    assert row.ctr == 0.0
    assert row.cpc is None
    assert row.acos is None
    assert row.roas is None
    assert row.cvr is None
    assert row.aov is None


def test_summarize_totals_from_sample():
    performances = _ingest_sample()
    summary = targeting_report_service.summarize(performances)

    # Only "wine saver" (PHRASE) has any cost in the fixture; no keyword
    # has any sales or purchases yet.
    assert summary.total_spend == 0.65
    assert summary.total_sales == 0.0
    assert summary.total_purchases == 0


def test_summarize_blended_acos_is_none_when_there_are_no_sales():
    performances = _ingest_sample()
    summary = targeting_report_service.summarize(performances)

    # Undefined when total sales is zero, not a fabricated 0.
    assert summary.blended_acos is None


def test_summarize_blended_acos_with_sales():
    performances = [
        _make_performance(keyword="a", cost=10.0, sales=50.0, purchases=2),
        _make_performance(keyword="b", cost=5.0, sales=0.0, purchases=0),
    ]
    summary = targeting_report_service.summarize(performances)

    assert summary.total_spend == 15.0
    assert summary.total_sales == 50.0
    assert summary.total_purchases == 2
    assert summary.blended_acos == 15.0 / 50.0


def test_summarize_empty_list():
    summary = targeting_report_service.summarize([])

    assert summary.total_spend == 0.0
    assert summary.total_sales == 0.0
    assert summary.total_purchases == 0
    assert summary.blended_acos is None
