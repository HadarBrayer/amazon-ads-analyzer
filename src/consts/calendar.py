from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class AmazonEvent:
    name: str
    start_date: date
    end_date: date


# Confirmed 2026 Amazon shopping events, in chronological order.
AMAZON_EVENTS_2026: list[AmazonEvent] = [
    AmazonEvent("Big Spring Sale", date(2026, 3, 25), date(2026, 3, 31)),
    AmazonEvent("Mother's Day Sale", date(2026, 5, 1), date(2026, 5, 12)),
    AmazonEvent("Prime Day", date(2026, 6, 23), date(2026, 6, 26)),
    AmazonEvent("Prime Big Deal Days", date(2026, 10, 6), date(2026, 10, 7)),
    AmazonEvent("Black Friday", date(2026, 11, 27), date(2026, 11, 27)),
    AmazonEvent("Cyber Monday", date(2026, 11, 30), date(2026, 11, 30)),
]

# Only surface an upcoming event once it's this close, to avoid noise.
UPCOMING_EVENT_WINDOW_DAYS = 30
