import csv
import io
from dataclasses import dataclass

REQUIRED_COLUMNS = [
    "Campaign ID",
    "Campaign name",
    "Ad group ID",
    "Ad group name",
    "Targeting",
    "Targeting match type",
    "Target ID",
    "Target bid",
    "Target status",
    "Impressions",
    "Clicks",
    "Total cost",
    "Purchases",
    "Sales",
    "Units sold",
]


@dataclass
class RawTargetingRow:
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


def _unescape_id(value: str) -> str:
    value = value.strip()
    if value.startswith('="') and value.endswith('"'):
        return value[2:-1]
    return value


def _parse_float(value: str) -> float | None:
    value = value.strip()
    if not value:
        return None
    return float(value)


def _parse_int(value: str) -> int:
    value = value.strip()
    if not value:
        return 0
    return int(float(value))


def _decode(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Amazon reports re-saved through Excel on Windows are commonly
        # written in the system codepage (Windows-1252) instead of UTF-8.
        try:
            return file_bytes.decode("cp1252")
        except UnicodeDecodeError as exc:
            raise ValueError(
                "Couldn't read this file as text. Make sure it's a CSV export "
                "of the Sponsored Products Targeting report, not a different "
                "file type (e.g. .xlsx)."
            ) from exc


def parse(file_bytes: bytes) -> list[RawTargetingRow]:
    text = _decode(file_bytes)
    reader = csv.DictReader(io.StringIO(text))

    fieldnames = set(reader.fieldnames or [])
    missing = [col for col in REQUIRED_COLUMNS if col not in fieldnames]
    if missing:
        raise ValueError(
            "This file doesn't look like a Sponsored Products Targeting "
            f"report — missing expected column(s): {', '.join(missing)}."
        )

    rows: list[RawTargetingRow] = []
    for record in reader:
        keyword = record.get("Targeting", "").strip()
        if not keyword:
            # Amazon includes ad-group subtotal rows with a blank "Targeting"
            # value in this export; they aren't real keyword targets.
            continue

        rows.append(
            RawTargetingRow(
                campaign_id=_unescape_id(record["Campaign ID"]),
                campaign_name=record["Campaign name"].strip(),
                ad_group_id=_unescape_id(record["Ad group ID"]),
                ad_group_name=record["Ad group name"].strip(),
                target_id=_unescape_id(record["Target ID"]),
                keyword=keyword,
                match_type=record["Targeting match type"].strip(),
                bid=_parse_float(record["Target bid"]),
                status=record["Target status"].strip(),
                impressions=_parse_int(record["Impressions"]),
                clicks=_parse_int(record["Clicks"]),
                cost=_parse_float(record["Total cost"]) or 0.0,
                sales=_parse_float(record["Sales"]) or 0.0,
                purchases=_parse_int(record["Purchases"]),
                units_sold=_parse_int(record["Units sold"]),
            )
        )
    return rows
