from typing import Dict, List, Optional
from pydantic import BaseModel


class DailyClickPoint(BaseModel):
    date: str
    clicks: int


class AnalyticsResponse(BaseModel):
    short_code: str
    total_clicks: int
    unique_visitors: int
    devices: Dict[str, int]
    browsers: Dict[str, int]
    countries: Dict[str, int]
    referrers: Dict[str, int]
    daily_clicks: List[DailyClickPoint]
