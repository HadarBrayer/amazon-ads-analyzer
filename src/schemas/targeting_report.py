from pydantic import BaseModel


class KeywordPerformance(BaseModel):
    campaign_id: str
    campaign_name: str
    ad_group_id: str
    ad_group_name: str
    target_id: str
    keyword: str
    match_type: str
    bid: float | None
    status: str

    impressions: int
    clicks: int
    cost: float
    sales: float
    purchases: int
    units_sold: int

    ctr: float | None
    cpc: float | None
    acos: float | None
    roas: float | None
    cvr: float | None
    aov: float | None


class TargetingReportSummary(BaseModel):
    total_spend: float
    total_sales: float
    total_purchases: int
    blended_acos: float | None
