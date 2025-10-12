from dataclasses import dataclass
from typing import Optional


@dataclass
class HistoricalPriceLight:
    """Light historical price data model."""
    date: str
    close: float
    volume: int


@dataclass
class HistoricalPriceFull:
    """Full historical price data model."""
    date: str
    open: float
    high: float
    low: float
    close: float
    adj_close: float
    volume: int
    unadjusted_volume: int
    change: float
    change_percent: float
    vwap: float
    label: str
    change_over_time: float


@dataclass
class IntradayPrice:
    """Intraday price data model for various time intervals."""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int