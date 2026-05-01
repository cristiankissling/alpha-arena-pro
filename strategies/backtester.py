"""
strategies/backtester.py
Motor de backtesting con soporte para múltiples estrategias y métricas profesionales.
"""
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from config.logger import logger
from strategies.technical import TechnicalAnalyzer


@dataclass
class BacktestTrade:
    entry_date:  str
    exit_date:   str
    ticker:      str
    side:        str
    entry_price: float
    exit_price:  float
    quantity:    int
    pnl:         float
    pnl_pct:     float
    commission:  float


@dataclass
class BacktestResult:
    strategy:          str
    ticker:            str
    initial_capital:   float
    final_capital:     float
    total_return_pct:  float
    annual_return_pct: float
    sharpe_ratio:      float
    sortino_ratio:     float
    max_drawdown_pct:  float
    calmar_ratio:      float
    win_rate:          float
    profit_factor:     float
    total_trades:      int
    winning_trades:    int
    losing_trades:     int
    avg_win_pct:       float
    avg_loss_pct:      float
    largest_win_pct:   float
    largest_loss_pct:  float
    avg_holding_days:  float
    trades:            List[BacktestTrade] = field(default_factory=list)
    equity_curve:      Optional[pd.Series] = None
    drawdown_curve:    Optional[pd.Series] = None

    def summary_dict(self) -> Dict:
        return {
            "Estrategia":       self.strategy,
            "Capital Inicial":  f"${self.initial_capital:,.0f}",
            "Capital Final":    f"${self.final_capital:,.0f}",
            "Retorno Total":    f"{self.total_return_pct:.2f}%",
            "Retorno Anual":    f"{self.annual_return_pct:.2f}%",
            "Sharpe Ratio":     f"{self.sharpe_ratio:.2f}",
            "Sortino Ratio":    f"{self.sortino_ratio:.2f}",
            "Max Drawdown":     f"{self.max_drawdown_pct:.2f}%",
            "Calmar Ratio":     f"{self.calmar_ratio:.2f}",
            "Win Rate":         f"{self.win_rate:.1%}",
            "Profit Factor":    f"{self.profit_factor:.2f}",
            "Total Trades":     str(self.total_trades),
            "Ganadores":        str(self.winning_trades),
            "Perdedores":       str(self.losing_trades),
        }


class Backtester:
    """
    Motor de backtesting.
    Soporta: momentum, mean_reversion, technical (TA completo), ml_based (usando features).
    """

    COMMISSION = 0.0006   # 0.06% por lado (BYMA + comisión broker típica Argentina)

    def __init__(self, initial_capital: float = 1_000_000.0):
        self.initial_capital = initial_capital
        self.ta = TechnicalAnalyzer()

    def run(
        self,
        df: pd.DataFrame,
        ticker: str = "TICKER",
        strategy: str = "technical",
        position_size_pct: float = 0.10,
        **params,
    ) -> BacktestResult:
        """Punto de entrada principal."""
        if df.empty or len(df) < 50:
            raise ValueError(f"Datos insuficientes: {len(df)} filas")

        strategies = {
            "momentum":      self._momentum_signals,
            "mean_reversion": self._mean_reversion_signals,
            "technical":     self._technical_signals,
        }

        if strategy not in strategies:
            raise ValueError(f"Estrategia desconocida: {strategy}")

        signal_fn = strategies[strategy]
        df_with_signals = signal_fn(df.copy(), **params)

        return self._run_simulation(
            df=df_with_signals,
            ticker=ticker,
            strategy=strategy,
            position_size_pct=position_size_pct,
        )

    # ── Generadores de señales ─────────────────────────────────

    def _momentum_signals(self, df: pd.DataFrame, lookback: int = 20, threshold: float = 0.03) -> pd.DataFrame:
        df["signal"] = 0
        mom = df["Close"].pct_change(lookback)
        df.loc[mom > threshold,  "signal"] = 1
        df.loc[mom < -threshold, "signal"] = -1
        return df

    def _mean_reversion_signals(self, df: pd.DataFrame, window: int = 20, std_mult: float = 2.0) -> pd.DataFrame:
        sma = df["Close"].rolling(window).mean()
        std = df["Close"].rolling(window).std()
        df["signal"] = 0
        df.loc[df["Close"] < sma - std_mult * std, "signal"] =  1   # sobreventa
        df.loc[df["Close"] > sma + std_mult * std, "signal"] = -1   # sobrecompra
        return df

    def _technical_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Usa el motor TA completo para generar señales."""
        df_ind = self.ta._add_all_indicators(df.copy())

        signals = []
        window_size = 50

        for i in range(window_size, len(df_ind)):
            window = df_ind.iloc[:i+1]
            result = self.ta.analyze(window)
            if result.signal == "BUY":
                signals.append(1)
            elif result.signal == "SELL":
                signals.append(-1)
            else:
                signals.append(0)

        # Pad con zeros para las primeras filas
        pad = [0] * window_size
        df["signal"] = pad + signals
        return df

    # ── Simulación ─────────────────────────────────────────────

    def _run_simulation(
        self,
        df: pd.DataFrame,
        ticker: str,
        strategy: str,
        position_size_pct: float,
    ) -> BacktestResult:

        capital   = self.initial_capital
        position  = 0      # cantidad de acciones
        entry_px  = 0.0
        entry_dt  = None
        trades    = []
        equity    = []

        for i in range(1, len(df)):
            close  = float(df["Close"].iloc[i])
            signal = int(df["signal"].iloc[i - 1])  # señal del día anterior
            date   = str(df.index[i])

            # Cerrar posición si cambia la señal
            if position != 0:
                should_close = (
                    (position > 0 and signal <= -1) or
                    (position < 0 and signal >= 1) or
                    signal == 0
                )
                if should_close:
                    comm = abs(position * close) * self.COMMISSION
                    if position > 0:
                        pnl = (close - entry_px) * position - comm
                    else:
                        pnl = (entry_px - close) * abs(position) - comm

                    pnl_pct = pnl / (abs(position) * entry_px) * 100 if entry_px else 0

                    trades.append(BacktestTrade(
                        entry_date=str(entry_dt),
                        exit_date=date,
                        ticker=ticker,
                        side="BUY" if position > 0 else "SELL",
                        entry_price=round(entry_px, 2),
                        exit_price=round(close, 2),
                        quantity=abs(position),
                        pnl=round(pnl, 2),
                        pnl_pct=round(pnl_pct, 2),
                        commission=round(comm, 2),
                    ))

                    capital  += pnl
                    position  = 0
                    entry_px  = 0.0

            # Abrir nueva posición
            if position == 0 and signal != 0:
                invest = capital * position_size_pct
                size   = int(invest / close)
                if size > 0:
                    comm      = size * close * self.COMMISSION
                    position  = size if signal > 0 else -size
                    entry_px  = close
                    entry_dt  = date
                    capital  -= comm

            # Valor del portfolio
            mark_to_market = position * close if close > 0 else 0
            equity.append(capital + mark_to_market)

        # Cerrar posición abierta al final
        if position != 0 and len(df) > 0:
            close = float(df["Close"].iloc[-1])
            comm  = abs(position * close) * self.COMMISSION
            pnl   = (close - entry_px) * position - comm if position > 0 else (entry_px - close) * abs(position) - comm
            capital += pnl

        # ── Métricas ─────────────────────────────────────────────
        equity_series = pd.Series(equity, index=df.index[1:len(equity)+1])
        if equity_series.empty:
            equity_series = pd.Series([self.initial_capital])

        final_capital  = equity_series.iloc[-1]
        total_ret_pct  = (final_capital / self.initial_capital - 1) * 100
        n_years        = len(df) / 252
        annual_ret_pct = ((final_capital / self.initial_capital) ** (1 / n_years) - 1) * 100 if n_years > 0 else 0

        # Sharpe y Sortino
        daily_rets = equity_series.pct_change().dropna()
        rf_daily   = 0.0  # tasa libre de riesgo (simplificado)

        excess = daily_rets - rf_daily
        sharpe = (excess.mean() / excess.std() * np.sqrt(252)) if excess.std() > 0 else 0
        downside = excess[excess < 0].std()
        sortino = (excess.mean() / downside * np.sqrt(252)) if downside > 0 else 0

        # Drawdown
        rolling_max  = equity_series.expanding().max()
        drawdown     = (equity_series - rolling_max) / rolling_max * 100
        max_dd       = abs(drawdown.min())
        calmar       = annual_ret_pct / max_dd if max_dd > 0 else 0

        # Trade stats
        pnls    = [t.pnl for t in trades]
        winners = [p for p in pnls if p > 0]
        losers  = [p for p in pnls if p <= 0]

        win_rate      = len(winners) / len(pnls) if pnls else 0
        profit_factor = abs(sum(winners) / sum(losers)) if losers and sum(losers) != 0 else float("inf")
        avg_win_pct   = np.mean([t.pnl_pct for t in trades if t.pnl > 0]) if winners else 0
        avg_loss_pct  = np.mean([t.pnl_pct for t in trades if t.pnl <= 0]) if losers else 0
        largest_win   = max((t.pnl_pct for t in trades if t.pnl > 0), default=0)
        largest_loss  = min((t.pnl_pct for t in trades if t.pnl <= 0), default=0)

        return BacktestResult(
            strategy=strategy,
            ticker=ticker,
            initial_capital=self.initial_capital,
            final_capital=round(final_capital, 2),
            total_return_pct=round(total_ret_pct, 2),
            annual_return_pct=round(annual_ret_pct, 2),
            sharpe_ratio=round(sharpe, 2),
            sortino_ratio=round(sortino, 2),
            max_drawdown_pct=round(max_dd, 2),
            calmar_ratio=round(calmar, 2),
            win_rate=round(win_rate, 4),
            profit_factor=round(profit_factor, 2),
            total_trades=len(trades),
            winning_trades=len(winners),
            losing_trades=len(losers),
            avg_win_pct=round(avg_win_pct, 2),
            avg_loss_pct=round(avg_loss_pct, 2),
            largest_win_pct=round(largest_win, 2),
            largest_loss_pct=round(largest_loss, 2),
            avg_holding_days=0,
            trades=trades,
            equity_curve=equity_series,
            drawdown_curve=drawdown,
        )


# Instancia global
backtester = Backtester()
