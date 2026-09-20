import csv
import io
from dataclasses import dataclass

from src.consts.cerebro import CEREBRO_FIXED_COLUMNS

REQUIRED_COLUMNS = [
    "Keyword Phrase",
    "Search Volume",
    "Search Volume Trend",
    "H10 PPC Sugg. Bid",
    "Competing Products",
    "Title Density",
    "Organic",
    "Sponsored",
    "Position (Rank)",
]


@dataclass
class RawCerebroRow:
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


def _decode(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            return file_bytes.decode("cp1252")
        except UnicodeDecodeError as exc:
            raise ValueError(
                "Couldn't read this file as text. Make sure it's a Helium 10 "
                "Cerebro CSV export."
            ) from exc


def _parse_int(value: str) -> int | None:
    value = value.strip()
    if not value or value == "-":
        return None
    return int(float(value))


def _parse_float(value: str) -> float | None:
    value = value.strip()
    if not value or value == "-":
        return None
    return float(value)


def _parse_bool(value: str) -> bool:
    return value.strip() == "1"


def parse(file_bytes: bytes) -> list[RawCerebroRow]:
    text = _decode(file_bytes)
    reader = csv.DictReader(io.StringIO(text))

    fieldnames = set(reader.fieldnames or [])
    missing = [col for col in REQUIRED_COLUMNS if col not in fieldnames]
    if missing:
        raise ValueError(
            "This file doesn't look like a Helium 10 Cerebro export — missing "
            f"expected column(s): {', '.join(missing)}."
        )

    asin_columns = sorted(fieldnames - CEREBRO_FIXED_COLUMNS)

    rows: list[RawCerebroRow] = []
    for record in reader:
        keyword = record.get("Keyword Phrase", "").strip()
        if not keyword:
            continue

        rows.append(
            RawCerebroRow(
                keyword=keyword,
                search_volume=_parse_int(record["Search Volume"]) or 0,
                search_volume_trend=_parse_int(record["Search Volume Trend"]),
                suggested_bid=_parse_float(record["H10 PPC Sugg. Bid"]),
                competing_products=_parse_int(record["Competing Products"]),
                title_density=_parse_int(record["Title Density"]),
                is_organic=_parse_bool(record["Organic"]),
                is_sponsored=_parse_bool(record["Sponsored"]),
                position_rank=_parse_int(record["Position (Rank)"]),
                competitor_ranks={asin: _parse_int(record[asin]) for asin in asin_columns},
            )
        )
    return rows
