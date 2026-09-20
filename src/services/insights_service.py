from datetime import date

from src.consts.calendar import AMAZON_EVENTS_2026, UPCOMING_EVENT_WINDOW_DAYS
from src.consts.insights import CTR_HIGH_MULTIPLIER, CTR_LOW_MULTIPLIER, CTR_MIN_IMPRESSIONS
from src.consts.strategy import StrategyMode
from src.schemas.strategy import StrategyParams
from src.schemas.targeting_report import KeywordPerformance, TargetingReportSummary


def spend_insights(
    performances: list[KeywordPerformance],
    summary: TargetingReportSummary,
    strategy: StrategyParams,
) -> list[str]:
    if not performances:
        return []

    insights: list[str] = []

    top = max(performances, key=lambda p: p.cost)
    if top.cost > 0:
        if top.acos is None:
            efficiency = "hasn't generated any sales yet"
        elif top.acos > strategy.target_acos:
            efficiency = f"is running above your {strategy.target_acos:.0%} target ACOS"
        else:
            efficiency = f"is running within your {strategy.target_acos:.0%} target ACOS"
        insights.append(
            f"**{top.keyword}** is your biggest spender (${top.cost:,.2f}) and {efficiency}."
        )

        if summary.total_spend > 0:
            share = top.cost / summary.total_spend
            insights.append(f"It accounts for {share:.0%} of your total spend.")

    zero_sale_spenders = [p for p in performances if p.cost > 0 and p.sales == 0]
    if zero_sale_spenders:
        count = len(zero_sale_spenders)
        if strategy.mode == StrategyMode.GROWTH:
            insights.append(
                f"{count} keyword(s) are spending with no sales yet — expected while you build "
                "sales velocity early on; watch total spend rather than pausing them yet."
            )
        else:
            insights.append(
                f"{count} keyword(s) are spending with zero sales — consider lowering bids or "
                "pausing to protect margin."
            )

    return insights


def acos_insights(
    performances: list[KeywordPerformance],
    summary: TargetingReportSummary,
    strategy: StrategyParams,
) -> list[str]:
    insights: list[str] = []

    if summary.blended_acos is None:
        if strategy.mode == StrategyMode.GROWTH:
            insights.append(
                "No sales yet, so blended ACOS isn't measurable — that's normal in growth mode "
                "while you spend to build initial traction and ranking."
            )
        else:
            insights.append(
                "No sales yet, so blended ACOS isn't measurable. Without conversions, this spend "
                "isn't currently paying for itself."
            )
        return insights

    if summary.blended_acos > strategy.target_acos:
        insights.append(
            f"Blended ACOS ({summary.blended_acos:.0%}) is above your "
            f"{strategy.target_acos:.0%} target."
        )
    else:
        insights.append(
            f"Blended ACOS ({summary.blended_acos:.0%}) is within your "
            f"{strategy.target_acos:.0%} target."
        )

    with_acos = [p for p in performances if p.acos is not None]
    above = [p for p in with_acos if p.acos > strategy.target_acos]
    below = [p for p in with_acos if p.acos <= strategy.target_acos]

    if with_acos:
        if strategy.mode == StrategyMode.GROWTH and above:
            insights.append(
                f"{len(above)} of {len(with_acos)} keywords with sales are above target — in "
                "growth mode that can be fine if you're intentionally paying for early traction."
            )
        else:
            insights.append(
                f"{len(above)} of {len(with_acos)} keywords with sales are above target, "
                f"{len(below)} are at or below."
            )

        best = min(with_acos, key=lambda p: p.acos)
        worst = max(with_acos, key=lambda p: p.acos)
        if best.keyword != worst.keyword:
            insights.append(
                f"**{best.keyword}** is your most efficient keyword at {best.acos:.0%} ACOS; "
                f"**{worst.keyword}** is your least efficient at {worst.acos:.0%}."
            )

    return insights


def ctr_insights(performances: list[KeywordPerformance]) -> list[str]:
    visible = [p for p in performances if p.impressions > 0]
    if not visible:
        return []

    total_impressions = sum(p.impressions for p in visible)
    total_clicks = sum(p.clicks for p in visible)
    if total_impressions == 0:
        return []
    avg_ctr = total_clicks / total_impressions

    insights = [f"Average CTR across all keywords is {avg_ctr:.1%}."]

    if avg_ctr > 0:
        low_ctr = [
            p
            for p in visible
            if p.impressions >= CTR_MIN_IMPRESSIONS
            and p.ctr is not None
            and p.ctr < avg_ctr * CTR_LOW_MULTIPLIER
        ]
        if low_ctr:
            worst = min(low_ctr, key=lambda p: p.ctr)
            insights.append(
                f"**{worst.keyword}** gets real visibility ({worst.impressions} impressions) "
                f"but only a {worst.ctr:.1%} CTR, well below your {avg_ctr:.1%} average. High "
                "impressions with a low click rate isn't on its own a reason to raise the bid "
                "— it's worth reviewing relevance, listing quality, price, or placement first."
            )
            if len(low_ctr) > 1:
                insights.append(
                    f"{len(low_ctr)} keyword(s) show this same pattern — visible but not "
                    "compelling enough to click."
                )

    strong_ctr = [
        p
        for p in visible
        if p.impressions >= CTR_MIN_IMPRESSIONS
        and p.ctr is not None
        and p.ctr > avg_ctr * CTR_HIGH_MULTIPLIER
    ]
    if strong_ctr:
        best = max(strong_ctr, key=lambda p: p.ctr)
        insights.append(
            f"**{best.keyword}** stands out with a {best.ctr:.1%} CTR on {best.impressions} "
            "impressions — whatever's showing for this search is resonating well."
        )

    return insights


def overall_recommendation(
    performances: list[KeywordPerformance],
    summary: TargetingReportSummary,
    strategy: StrategyParams,
) -> list[str]:
    if not performances:
        return []

    lines: list[str] = []

    if summary.blended_acos is None:
        if strategy.mode == StrategyMode.GROWTH:
            lines.append(
                "You have impressions and clicks but no sales yet, so ACOS can't be judged. "
                "In growth mode that's a normal early phase — the priority is proving "
                "keywords can convert at all before optimizing for efficiency."
            )
        else:
            lines.append(
                "You have impressions and clicks but no sales yet, so ACOS can't be judged. "
                "Consider trimming spend on the keywords with the most clicks and zero "
                "conversions until you have evidence they can convert."
            )
    elif summary.blended_acos > strategy.target_acos:
        if strategy.mode == StrategyMode.GROWTH:
            lines.append(
                f"Blended ACOS ({summary.blended_acos:.0%}) is above your "
                f"{strategy.target_acos:.0%} target — acceptable if you're intentionally "
                "investing in growth, but worth capping to your worst offenders rather than "
                "letting it run unchecked everywhere."
            )
        else:
            lines.append(
                f"Blended ACOS ({summary.blended_acos:.0%}) is above your "
                f"{strategy.target_acos:.0%} target — prioritize trimming bids on your least "
                "efficient keywords first rather than cutting across the board."
            )
    else:
        lines.append(
            f"Blended ACOS ({summary.blended_acos:.0%}) is within your "
            f"{strategy.target_acos:.0%} target — there's headroom to push harder on your "
            "most efficient keywords rather than just holding steady."
        )

    visible = [p for p in performances if p.impressions > 0]
    total_impressions = sum(p.impressions for p in visible)
    total_clicks = sum(p.clicks for p in visible)
    if total_impressions > 0:
        avg_ctr = total_clicks / total_impressions
        if avg_ctr > 0:
            low_ctr_high_vis = [
                p
                for p in visible
                if p.impressions >= CTR_MIN_IMPRESSIONS
                and p.ctr is not None
                and p.ctr < avg_ctr * CTR_LOW_MULTIPLIER
            ]
            if low_ctr_high_vis:
                lines.append(
                    f"{len(low_ctr_high_vis)} keyword(s) get real visibility but a low click "
                    "rate — before touching bids there, check the listing itself (main image, "
                    "price, title), since that's more likely the cause than the bid."
                )

    return lines


def calendar_insights(strategy: StrategyParams, today: date | None = None) -> list[str]:
    today = today or date.today()

    for event in AMAZON_EVENTS_2026:
        if event.start_date <= today <= event.end_date:
            return [
                f"**{event.name}** is happening right now (through "
                f"{event.end_date.strftime('%b %d')}) — a good window to keep budget flowing "
                "on your efficient keywords while demand is elevated."
            ]

        if event.start_date > today:
            days_until = (event.start_date - today).days
            if days_until > UPCOMING_EVENT_WINDOW_DAYS:
                return []

            when = event.start_date.strftime("%b %d")
            if strategy.mode == StrategyMode.GROWTH:
                return [
                    f"**{event.name}** starts in {days_until} day(s) ({when}) — consider "
                    "raising bids on your efficient keywords now to build momentum and "
                    "ranking before it hits."
                ]
            return [
                f"**{event.name}** starts in {days_until} day(s) ({when}) — worth a "
                "temporary bid increase on your most efficient keywords only, to capture "
                "extra demand without hurting margin."
            ]

    return []
