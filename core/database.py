"""
core/database.py
Modelos SQLAlchemy y manager de base de datos async.
"""
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from sqlalchemy import (
    Column, Integer, String, Float, DateTime,
    Boolean, JSON, Text, Index, select, func, desc, and_
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config.settings import settings
from config.logger import logger


# ── ORM Base ────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Modelos ──────────────────────────────────────────────────────

class Trade(Base):
    __tablename__ = "trades"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    ticker       = Column(String(20), nullable=False, index=True)
    side         = Column(String(4), nullable=False)          # BUY / SELL
    quantity     = Column(Integer, nullable=False)
    entry_price  = Column(Float, nullable=False)
    exit_price   = Column(Float)
    status       = Column(String(10), default="OPEN")         # OPEN / CLOSED / CANCELLED
    entry_time   = Column(DateTime, default=datetime.utcnow)
    exit_time    = Column(DateTime)
    pnl          = Column(Float, default=0.0)
    pnl_pct      = Column(Float, default=0.0)
    stop_loss    = Column(Float)
    take_profit  = Column(Float)
    commission   = Column(Float, default=0.0)
    strategy     = Column(String(50))
    signal_score = Column(Float)                               # score 0-1 del ML
    trade_meta   = Column(JSON)                                # indicadores al momento

    __table_args__ = (
        Index("ix_trades_ticker_status", "ticker", "status"),
    )


class Signal(Base):
    __tablename__ = "signals"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    ticker      = Column(String(20), nullable=False, index=True)
    signal_type = Column(String(10), nullable=False)           # BUY / SELL / HOLD
    score       = Column(Float)                                 # 0-1 confianza
    price       = Column(Float)
    timestamp   = Column(DateTime, default=datetime.utcnow, index=True)
    reason      = Column(Text)
    indicators  = Column(JSON)
    ml_proba    = Column(Float)                                 # probabilidad ML
    ta_score    = Column(Float)                                 # score análisis técnico


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id        = Column(Integer, primary_key=True, autoincrement=True)
    ticker    = Column(String(20), nullable=False, index=True)
    price     = Column(Float)
    change_pct = Column(Float)
    volume    = Column(Integer)
    high      = Column(Float)
    low       = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    market    = Column(String(10))                              # MERVAL / CEDEAR


class MLModel(Base):
    __tablename__ = "ml_models"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    ticker      = Column(String(20), nullable=False, unique=True)
    model_path  = Column(String(200))
    trained_at  = Column(DateTime, default=datetime.utcnow)
    accuracy    = Column(Float)
    features    = Column(JSON)
    params      = Column(JSON)
    n_samples   = Column(Integer)


# ── Manager ──────────────────────────────────────────────────────

class DatabaseManager:
    def __init__(self):
        self._engine = None
        self._session_factory = None

    async def initialize(self):
        """Crear engine y tablas."""
        # Asegurar que el directorio existe
        db_path = Path(settings.data_dir) / "trading.db"
        db_url = f"sqlite+aiosqlite:///{db_path}"

        self._engine = create_async_engine(
            db_url,
            echo=settings.debug,
            connect_args={"check_same_thread": False},
        )
        self._session_factory = sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False
        )

        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info(f"✅ Base de datos inicializada: {db_path}")

    def get_session(self) -> AsyncSession:
        return self._session_factory()

    # ── Trades ─────────────────────────────────────────────────

    async def save_trade(self, trade_data: Dict) -> Trade:
        async with self.get_session() as session:
            trade = Trade(**trade_data)
            session.add(trade)
            await session.commit()
            await session.refresh(trade)
            return trade

    async def close_trade(self, trade_id: int, exit_price: float, pnl: float, pnl_pct: float):
        async with self.get_session() as session:
            result = await session.execute(select(Trade).where(Trade.id == trade_id))
            trade = result.scalar_one_or_none()
            if trade:
                trade.exit_price = exit_price
                trade.exit_time = datetime.utcnow()
                trade.pnl = pnl
                trade.pnl_pct = pnl_pct
                trade.status = "CLOSED"
                await session.commit()

    async def get_open_trades(self) -> List[Trade]:
        async with self.get_session() as session:
            result = await session.execute(
                select(Trade).where(Trade.status == "OPEN").order_by(desc(Trade.entry_time))
            )
            return result.scalars().all()

    async def get_recent_trades(self, limit: int = 50) -> List[Trade]:
        async with self.get_session() as session:
            result = await session.execute(
                select(Trade).order_by(desc(Trade.entry_time)).limit(limit)
            )
            return result.scalars().all()

    async def get_trade_stats(self) -> Dict:
        async with self.get_session() as session:
            # Total trades
            total = await session.execute(select(func.count(Trade.id)))
            total_count = total.scalar() or 0

            # Closed trades
            closed = await session.execute(
                select(Trade).where(Trade.status == "CLOSED")
            )
            closed_trades = closed.scalars().all()

            if not closed_trades:
                return {
                    "total_trades": total_count,
                    "closed_trades": 0,
                    "win_rate": 0.0,
                    "total_pnl": 0.0,
                    "avg_pnl": 0.0,
                    "best_trade": 0.0,
                    "worst_trade": 0.0,
                }

            pnls = [t.pnl for t in closed_trades if t.pnl is not None]
            winners = [p for p in pnls if p > 0]

            return {
                "total_trades": total_count,
                "closed_trades": len(closed_trades),
                "win_rate": len(winners) / len(pnls) if pnls else 0.0,
                "total_pnl": sum(pnls),
                "avg_pnl": sum(pnls) / len(pnls) if pnls else 0.0,
                "best_trade": max(pnls) if pnls else 0.0,
                "worst_trade": min(pnls) if pnls else 0.0,
            }

    # ── Signals ────────────────────────────────────────────────

    async def save_signal(self, signal_data: Dict) -> Signal:
        async with self.get_session() as session:
            signal = Signal(**signal_data)
            session.add(signal)
            await session.commit()
            await session.refresh(signal)
            return signal

    async def get_recent_signals(self, limit: int = 50, ticker: Optional[str] = None) -> List[Signal]:
        async with self.get_session() as session:
            query = select(Signal).order_by(desc(Signal.timestamp)).limit(limit)
            if ticker:
                query = select(Signal).where(Signal.ticker == ticker).order_by(desc(Signal.timestamp)).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()

    # ── Market Snapshots ───────────────────────────────────────

    async def save_snapshot(self, data: Dict):
        async with self.get_session() as session:
            snap = MarketSnapshot(**data)
            session.add(snap)
            await session.commit()

    async def get_snapshots(self, ticker: str, limit: int = 100) -> List[MarketSnapshot]:
        async with self.get_session() as session:
            result = await session.execute(
                select(MarketSnapshot)
                .where(MarketSnapshot.ticker == ticker)
                .order_by(desc(MarketSnapshot.timestamp))
                .limit(limit)
            )
            return result.scalars().all()


# Instancia global
db = DatabaseManager()
