import math

from src.consts.cerebro import ESTIMATED_RESULTS_PER_PAGE
from src.repositories import cerebro_repository
from src.schemas.cerebro import CerebroKeywordRow


def ingest(file_bytes: bytes) -> list[CerebroKeywordRow]:
    raw_rows = cerebro_repository.parse(file_bytes)

    return [
        CerebroKeywordRow(
            keyword=row.keyword,
            search_volume=row.search_volume,
            search_volume_trend=row.search_volume_trend,
            suggested_bid=row.suggested_bid,
            competing_products=row.competing_products,
            title_density=row.title_density,
            is_organic=row.is_organic,
            is_sponsored=row.is_sponsored,
            position_rank=row.position_rank,
            competitor_ranks=row.competitor_ranks,
        )
        for row in raw_rows
    ]


def find_keyword(rows: list[CerebroKeywordRow], keyword: str) -> CerebroKeywordRow | None:
    target = keyword.strip().lower()
    if not target:
        return None
    return next((row for row in rows if row.keyword.lower() == target), None)


def opportunity_keywords(
    rows: list[CerebroKeywordRow],
    targeted_keywords: set[str],
    limit: int = 15,
) -> list[CerebroKeywordRow]:
    targeted = {k.strip().lower() for k in targeted_keywords}
    untapped = [row for row in rows if row.keyword.lower() not in targeted]
    return sorted(untapped, key=lambda row: row.search_volume, reverse=True)[:limit]


def estimate_page(rank: int) -> int:
    return max(1, math.ceil(rank / ESTIMATED_RESULTS_PER_PAGE))
