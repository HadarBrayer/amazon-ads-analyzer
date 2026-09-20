from pydantic import BaseModel


class CerebroKeywordRow(BaseModel):
    keyword: str
    search_volume: int
    search_volume_trend: int | None
    suggested_bid: float | None
    competing_products: int | None
    title_density: int | None
    is_organic: bool
    is_sponsored: bool
    position_rank: int | None
    competitor_ranks: dict[str, int | None]
