"""
config/settings.py
Configuración central del sistema de trading.
Compatible con entornos locales y Streamlit Cloud (read-only filesystem).
"""
import os
import sys
import tempfile
from typing import List, Optional, Literal
from pathlib import Path

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import Field
except ImportError:
    from pydantic import BaseSettings, Field

ROOT_DIR = Path(__file__).parent.parent

def _is_cloud() -> bool:
    return os.path.exists("/mount/src") or os.environ.get("STREAMLIT_CLOUD", "") == "1"

def _safe_dir(path: Path) -> Path:
    try:
        path.mkdir(exist_ok=True, parents=True)
    except Exception:
        pass
    return path

def _tmp_dir(name: str) -> Path:
    d = Path(tempfile.gettempdir()) / name
    return _safe_dir(d)


class Settings(BaseSettings):
    app_name: str = "Alpha Arena Pro"
    version: str = "2.0.0"
    environment: Literal["development", "production"] = "development"
    debug: bool = False

    database_url: str = ""  # se setea en __init__

    initial_capital: float = Field(default=1_000_000.0, gt=0)
    max_position_size_pct: float = Field(default=0.10, ge=0.01, le=0.30)
    risk_per_trade_pct: float = Field(default=0.02, ge=0.001, le=0.05)
    max_open_positions: int = Field(default=8, ge=1, le=20)
    stop_loss_pct: float = Field(default=0.05, ge=0.01, le=0.15)
    take_profit_pct: float = Field(default=0.12, ge=0.02, le=0.40)

    merval_universe: List[str] = Field(default=[
        "GGAL.BA", "YPFD.BA", "PAMP.BA", "TXAR.BA", "CEPU.BA",
        "BMA.BA", "SUPV.BA", "MIRG.BA", "VALO.BA", "LEDE.BA",
        "ALUA.BA", "BYMA.BA", "CRES.BA", "EDN.BA", "HARG.BA",
        "METR.BA", "TGNO4.BA", "TGSU2.BA", "TRAN.BA", "IRSA.BA",
    ])
    cedear_universe: List[str] = Field(default=[
        "AAPL",  "MSFT",  "GOOGL", "AMZN",  "NVDA",
        "META",  "TSLA",  "MELI",  "GLOB",  "BRK-B",
        "JPM",   "XOM",   "WMT",   "DIS",   "NFLX",
    ])

    trading_mode: Literal["backtest", "paper", "live"] = "paper"
    analysis_interval_seconds: int = Field(default=300, ge=60)
    top_opportunities: int = Field(default=10, ge=3, le=30)

    ml_lookback_days: int = Field(default=365, ge=60)
    ml_retrain_interval_hours: int = Field(default=24, ge=1)
    ml_min_confidence: float = Field(default=0.60, ge=0.50, le=0.95)

    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    enable_telegram_alerts: bool = False

    dashboard_port: int = Field(default=8501, ge=1024, le=65535)

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def model_post_init(self, __context):
        if not self.database_url:
            db_path = self.data_dir / "trading.db"
            object.__setattr__(self, "database_url", f"sqlite+aiosqlite:///{db_path}")

    @property
    def all_tickers(self) -> List[str]:
        return self.merval_universe + self.cedear_universe

    @property
    def data_dir(self) -> Path:
        return _tmp_dir("trading_data") if _is_cloud() else _safe_dir(ROOT_DIR / "data")

    @property
    def logs_dir(self) -> Path:
        return _tmp_dir("trading_logs") if _is_cloud() else _safe_dir(ROOT_DIR / "logs")

    @property
    def models_dir(self) -> Path:
        return _tmp_dir("trading_models") if _is_cloud() else _safe_dir(ROOT_DIR / "data" / "models")


try:
    settings = Settings()
except Exception as e:
    print(f"❌ Error cargando configuración: {e}")
    sys.exit(1)
