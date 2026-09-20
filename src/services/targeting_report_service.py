from src.schemas.targeting_report import KeywordPerformance, TargetingReportSummary
from src.repositories import targeting_report_repository


def _safe_div(numerator: float, denominator: float) -> float | None:
    if not denominator:
        return None
    return numerator / denominator


def ingest(file_bytes: bytes) -> list[KeywordPerformance]:
    raw_rows = targeting_report_repository.parse(file_bytes)

    return [
        KeywordPerformance(
            campaign_id=row.campaign_id,
            campaign_name=row.campaign_name,
            ad_group_id=row.ad_group_id,
            ad_group_name=row.ad_group_name,
            target_id=row.target_id,
            keyword=row.keyword,
            match_type=row.match_type,
            bid=row.bid,
            status=row.status,
            impressions=row.impressions,
            clicks=row.clicks,
            cost=row.cost,
            sales=row.sales,
            purchases=row.purchases,
            units_sold=row.units_sold,
            ctr=_safe_div(row.clicks, row.impressions),
            cpc=_safe_div(row.cost, row.clicks),
            acos=_safe_div(row.cost, row.sales),
            roas=_safe_div(row.sales, row.cost),
            cvr=_safe_div(row.purchases, row.clicks),
            aov=_safe_div(row.sales, row.purchases),
        )
        for row in raw_rows
    ]


def summarize(performances: list[KeywordPerformance]) -> TargetingReportSummary:
    total_spend = sum(p.cost for p in performances)
    total_sales = sum(p.sales for p in performances)
    total_purchases = sum(p.purchases for p in performances)

    return TargetingReportSummary(
        total_spend=total_spend,
        total_sales=total_sales,
        total_purchases=total_purchases,
        blended_acos=_safe_div(total_spend, total_sales),
    )
