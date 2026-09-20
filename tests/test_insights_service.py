from datetime import date

from src.consts.strategy import StrategyMode
from src.schemas.strategy import StrategyParams
from src.schemas.targeting_report import KeywordPerformance
from src.services import insights_service, targeting_report_service


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


def _summarize(performances: list[KeywordPerformance]):
    return targeting_report_service.summarize(performances)


def test_spend_insights_empty_when_no_performances():
    summary = _summarize([])
    strategy = StrategyParams(target_acos=0.80, mode=StrategyMode.PROFITABILITY)

    assert insights_service.spend_insights([], summary, strategy) == []


def test_spend_insights_names_top_spender_and_its_share():
    performances = [
        _make_performance(keyword="big", cost=90.0, sales=90.0, acos=1.0),
        _make_performance(keyword="small", cost=10.0, sales=50.0, acos=0.2),
    ]
    summary = _summarize(performances)
    strategy = StrategyParams(target_acos=0.80, mode=StrategyMode.PROFITABILITY)

    insights = insights_service.spend_insights(performances, summary, strategy)

    assert any("big" in i and "$90.00" in i for i in insights)
    assert any("90%" in i for i in insights)  # 90/100 share of total spend


def test_spend_insights_zero_sale_spenders_phrased_differently_by_mode():
    performances = [
        _make_performance(keyword="bleeding", cost=20.0, sales=0.0),
    ]
    summary = _summarize(performances)

    growth_insights = insights_service.spend_insights(
        performances, summary, StrategyParams(target_acos=0.80, mode=StrategyMode.GROWTH)
    )
    profitability_insights = insights_service.spend_insights(
        performances, summary, StrategyParams(target_acos=0.80, mode=StrategyMode.PROFITABILITY)
    )

    assert any("expected while you build" in i for i in growth_insights)
    assert any("pausing to protect margin" in i for i in profitability_insights)


def test_acos_insights_when_no_sales_at_all():
    performances = [_make_performance(keyword="new", cost=5.0, sales=0.0)]
    summary = _summarize(performances)

    growth_insights = insights_service.acos_insights(
        performances, summary, StrategyParams(target_acos=0.80, mode=StrategyMode.GROWTH)
    )
    profitability_insights = insights_service.acos_insights(
        performances, summary, StrategyParams(target_acos=0.80, mode=StrategyMode.PROFITABILITY)
    )

    assert any("normal in growth mode" in i for i in growth_insights)
    assert any("isn't currently paying for itself" in i for i in profitability_insights)


def test_acos_insights_identifies_best_and_worst_keyword():
    performances = [
        _make_performance(keyword="efficient", cost=10.0, sales=100.0, acos=0.1),
        _make_performance(keyword="inefficient", cost=100.0, sales=50.0, acos=2.0),
    ]
    summary = _summarize(performances)
    strategy = StrategyParams(target_acos=0.80, mode=StrategyMode.PROFITABILITY)

    insights = insights_service.acos_insights(performances, summary, strategy)

    assert any("efficient" in i and "inefficient" in i for i in insights)
    # blended ACOS here is (10+100)/(100+50) = 73%, below the 80% target
    assert any("within your 80% target" in i for i in insights)


def test_acos_insights_above_target_count_softened_in_growth_mode():
    performances = [
        _make_performance(keyword="over", cost=100.0, sales=50.0, acos=2.0),
    ]
    summary = _summarize(performances)

    growth_insights = insights_service.acos_insights(
        performances, summary, StrategyParams(target_acos=0.80, mode=StrategyMode.GROWTH)
    )

    assert any("growth mode that can be fine" in i for i in growth_insights)


def test_ctr_insights_empty_when_no_impressions():
    performances = [_make_performance(keyword="new", impressions=0)]

    assert insights_service.ctr_insights(performances) == []


def test_ctr_insights_reports_account_average():
    performances = [
        _make_performance(keyword="a", impressions=1000, clicks=100, ctr=0.10),
        _make_performance(keyword="b", impressions=1000, clicks=100, ctr=0.10),
    ]

    insights = insights_service.ctr_insights(performances)

    assert any("Average CTR" in i and "10.0%" in i for i in insights)


def test_ctr_insights_flags_high_impressions_low_ctr_without_recommending_bid_change():
    performances = [
        _make_performance(keyword="normal", impressions=100, clicks=10, ctr=0.10),
        _make_performance(keyword="invisible-clicker", impressions=1000, clicks=2, ctr=0.002),
    ]

    insights = insights_service.ctr_insights(performances)

    flagged = next(i for i in insights if "invisible-clicker" in i)
    assert "isn't on its own a reason to raise the bid" in flagged
    assert "relevance, listing quality, price, or placement" in flagged
    # Must not suggest bidding up despite the high impression count.
    assert "raise the bid" not in flagged.replace("isn't on its own a reason to raise the bid", "")


def test_ctr_insights_flags_standout_high_ctr_keyword():
    performances = [
        _make_performance(keyword="normal", impressions=100, clicks=10, ctr=0.10),
        _make_performance(keyword="normal2", impressions=100, clicks=10, ctr=0.10),
        _make_performance(keyword="star", impressions=100, clicks=40, ctr=0.40),
    ]

    insights = insights_service.ctr_insights(performances)

    assert any("star" in i and "resonating well" in i for i in insights)


def test_overall_recommendation_empty_when_no_performances():
    summary = _summarize([])
    strategy = StrategyParams(target_acos=0.80, mode=StrategyMode.PROFITABILITY)

    assert insights_service.overall_recommendation([], summary, strategy) == []


def test_overall_recommendation_no_sales_phrased_by_mode():
    performances = [_make_performance(keyword="new", impressions=100, clicks=10, cost=5.0, sales=0.0)]
    summary = _summarize(performances)

    growth = insights_service.overall_recommendation(
        performances, summary, StrategyParams(target_acos=0.80, mode=StrategyMode.GROWTH)
    )
    profitability = insights_service.overall_recommendation(
        performances, summary, StrategyParams(target_acos=0.80, mode=StrategyMode.PROFITABILITY)
    )

    assert any("normal early phase" in i for i in growth)
    assert any("trimming spend" in i for i in profitability)


def test_overall_recommendation_within_target_suggests_pushing_harder():
    performances = [
        _make_performance(keyword="good", cost=10.0, sales=100.0, acos=0.1),
    ]
    summary = _summarize(performances)
    strategy = StrategyParams(target_acos=0.80, mode=StrategyMode.PROFITABILITY)

    insights = insights_service.overall_recommendation(performances, summary, strategy)

    assert any("headroom to push harder" in i for i in insights)


def test_overall_recommendation_includes_ctr_signal_when_present():
    performances = [
        _make_performance(keyword="good", cost=10.0, sales=100.0, acos=0.1, impressions=100, clicks=10, ctr=0.10),
        _make_performance(keyword="invisible-clicker", impressions=1000, clicks=2, ctr=0.002),
    ]
    summary = _summarize(performances)
    strategy = StrategyParams(target_acos=0.80, mode=StrategyMode.PROFITABILITY)

    insights = insights_service.overall_recommendation(performances, summary, strategy)

    assert any("check the listing itself" in i for i in insights)


def test_calendar_insights_empty_when_next_event_is_far_away():
    strategy = StrategyParams(target_acos=0.80, mode=StrategyMode.PROFITABILITY)

    insights = insights_service.calendar_insights(strategy, today=date(2026, 1, 1))

    assert insights == []


def test_calendar_insights_empty_after_the_last_event_of_the_year():
    strategy = StrategyParams(target_acos=0.80, mode=StrategyMode.PROFITABILITY)

    insights = insights_service.calendar_insights(strategy, today=date(2026, 12, 15))

    assert insights == []


def test_calendar_insights_within_upcoming_window_phrased_by_mode():
    growth = StrategyParams(target_acos=0.80, mode=StrategyMode.GROWTH)
    profitability = StrategyParams(target_acos=0.80, mode=StrategyMode.PROFITABILITY)
    today = date(2026, 9, 20)  # 16 days before Prime Big Deal Days (Oct 6)

    growth_insights = insights_service.calendar_insights(growth, today=today)
    profitability_insights = insights_service.calendar_insights(profitability, today=today)

    assert any(
        "Prime Big Deal Days" in i and "16 day" in i and "build momentum" in i
        for i in growth_insights
    )
    assert any(
        "Prime Big Deal Days" in i and "16 day" in i and "temporary bid increase" in i
        for i in profitability_insights
    )


def test_calendar_insights_during_an_active_event():
    strategy = StrategyParams(target_acos=0.80, mode=StrategyMode.PROFITABILITY)

    insights = insights_service.calendar_insights(strategy, today=date(2026, 10, 7))

    assert any("Prime Big Deal Days" in i and "happening right now" in i for i in insights)
