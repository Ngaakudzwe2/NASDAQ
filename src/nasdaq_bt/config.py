from __future__ import annotations

from dataclasses import dataclass, field, fields
from pathlib import Path

import yaml


@dataclass
class StrategyConfig:
    entry_rule: str = "symmetric"
    ema_period: int = 12
    atr_period: int = 14
    open_time: str = "09:30"
    session_close: str = "16:00"
    min_body_atr: float = 0.0
    skip_weekdays: list = field(default_factory=list)
    stop_mode: str = "atr"
    stop_atr_mult: float = 1.5
    candle_stop_buffer: float = 1.0
    trail_atr_mult: float = 2.5
    breakeven_at_r: float = 0.0
    hold_overnight: bool = True


@dataclass
class RiskConfig:
    initial_equity: float = 10_000
    risk_pct: float = 0.5
    max_leverage: float = 20
    spread_points: float = 1.5
    entry_slippage_points: float = 1.0
    stop_slippage_points: float = 1.0
    swap_pct_per_year: float = 7.0


@dataclass
class DataConfig:
    csv_path: str = "data/NAS100_M5.csv"
    csv_timezone: str = "UTC"
    start: str | None = None
    end: str | None = None


@dataclass
class Config:
    data: DataConfig = field(default_factory=DataConfig)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    output_dir: str = "results"


def _fill(cls, raw: dict | None):
    raw = raw or {}
    known = {f.name for f in fields(cls)}
    unknown = set(raw) - known
    if unknown:
        raise ValueError(f"Unknown {cls.__name__} keys in config: {sorted(unknown)}")
    return cls(**raw)


def load_config(path: str | Path = "config.yaml") -> Config:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return Config(
        data=_fill(DataConfig, raw.get("data")),
        strategy=_fill(StrategyConfig, raw.get("strategy")),
        risk=_fill(RiskConfig, raw.get("risk")),
        output_dir=(raw.get("output") or {}).get("dir", "results"),
    )
