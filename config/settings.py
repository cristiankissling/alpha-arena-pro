"""
config/settings.py
Configuración central del sistema de trading.
"""
import os
import sys
from typing import List, Optional, Literal
from pathlib import Path

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import Field
except ImportError:
    from pydantic import BaseSettings, Field

# Directorio raíz del proyecto
ROOT_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    # ── Aplicación ──────────────────────────────────────────────
    app_name: str = "Alpha Arena Pro"
    version: str = "2.0.0"
    environment: Literal["development", "production"] = "development"
    debug: bool = False

    # ── Base de datos ────────────────────────────────────────────
    database_url: str = f"sqlite+aiosqlite:///{ROOT_DIR}/data/trading.db"

    # ── Capital y riesgo ─────────────────────────────────────────
    initial_capital: float = Field(default=1_000_000.0, gt=0)
    max_position_size_pct: float = Field(default=0.10, ge=0.01, le=0.30)   # 10% por posición
    risk_per_trade_pct: float = Field(default=0.02, ge=0.001, le=0.05)     # 2% riesgo por trade
    max_open_positions: int = Field(default=8, ge=1, le=20)
    stop_loss_pct: float = Field(default=0.05, ge=0.01, le=0.15)           # 5% stop loss
    take_profit_pct: float = Field(default=0.12, ge=0.02, le=0.40)         # 12% take profit

    # ── Universo de activos ──────────────────────────────────────
    # El sistema detecta dinámicamente las mejores oportunidades,
    # pero parte de este universo base.
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

    # ── Modo de trading ──────────────────────────────────────────
    trading_mode: Literal["backtest", "paper", "live"] = "paper"
    analysis_interval_seconds: int = Field(default=300, ge=60)    # cada 5 min
    top_opportunities: int = Field(default=10, ge=3, le=30)        # top N activos a mostrar

    # ── ML ───────────────────────────────────────────────────────
    ml_lookback_days: int = Field(default=365, ge=60)
    ml_retrain_interval_hours: int = Field(default=24, ge=1)
    ml_min_confidence: float = Field(default=0.60, ge=0.50, le=0.95)

    # ── Telegram ─────────────────────────────────────────────────
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    enable_telegram_alerts: bool = False

    # ── Dashboard ────────────────────────────────────────────────
    dashboard_port: int = Field(default=8501, ge=1024, le=65535)

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def all_tickers(self) -> List[str]:
        return self.merval_universe + self.cedear_universe

    @property
    def data_dir(self) -> Path:
        d = ROOT_DIR / "data"
        d.mkdir(exist_ok=True)
        return d

    @property
    def logs_dir(self) -> Path:
        d = ROOT_DIR / "logs"
        d.mkdir(exist_ok=True)
        return d

    @property
    def models_dir(self) -> Path:
        d = ROOT_DIR / "data" / "models"
        d.mkdir(exist_ok=True)
        return d


# ── Instancia global ─────────────────────────────────────────────
try:
    settings = Settings()
except Exception as e:
    print(f"❌ Error cargando configuración: {e}")
    sys.exit(1)
