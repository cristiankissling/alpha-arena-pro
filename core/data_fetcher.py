"""
core/data_fetcher.py
Fetcher de datos con caché, fallback y scanner dinámico de oportunidades.
"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

import yfinance as yf

from config.settings import settings
from config.logger import logger


# ── Cache simple en memoria ──────────────────────────────────────
class SimpleCache:
    def __init__(self):
        self._store: Dict[str, Tuple[Any, float]] = {}

    def get(self, key: str, ttl: int = 60):
        if key in self._store:
            value, ts = self._store[key]
            if time.time() - ts < ttl:
                return value
            del self._store[key]
        return None

    def set(self, key: str, value):
        self._store[key] = (value, time.time())

    def clear(self):
        self._store.clear()


from typing import Any
_cache = SimpleCache()


# ── Fetcher principal ────────────────────────────────────────────
class MarketDataFetcher:
    """
    Fetcher de datos de mercado.
    - Datos en tiempo real (con caché 30s)
    - Datos históricos para TA y ML
    - Scanner dinámico: detecta los mejores activos del momento
    """

    MERVAL_TICKERS = settings.merval_universe
    CEDEAR_TICKERS = settings.cedear_universe

    # ── Tiempo real ────────────────────────────────────────────

    def get_quote(self, ticker: str, ttl: int = 30) -> Dict:
        """Cotización actual con caché."""
        cached = _cache.get(f"quote:{ticker}", ttl)
        if cached:
            return cached

        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2d", interval="1m")

            if hist.empty:
                hist = stock.history(period="5d", interval="1d")

            if hist.empty:
                return self._empty_quote(ticker)

            price = float(hist["Close"].iloc[-1])
            prev  = float(hist["Close"].iloc[-2]) if len(hist) > 1 else price
            chg   = (price - prev) / prev * 100 if prev else 0

            result = {
                "ticker":   ticker,
                "price":    round(price, 2),
                "change":   round(chg, 2),
                "volume":   int(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else 0,
                "high":     round(float(hist["High"].max()), 2),
                "low":      round(float(hist["Low"].min()), 2),
                "open":     round(float(hist["Open"].iloc[0]), 2),
                "prev_close": round(prev, 2),
                "timestamp": datetime.now().isoformat(),
                "market":   "MERVAL" if ".BA" in ticker else "CEDEAR",
                "ok":       True,
            }
            _cache.set(f"quote:{ticker}", result)
            return result

        except Exception as e:
            logger.warning(f"Error quote {ticker}: {e}")
            return self._empty_quote(ticker)

    def _empty_quote(self, ticker: str) -> Dict:
        return {
            "ticker": ticker, "price": 0, "change": 0, "volume": 0,
            "high": 0, "low": 0, "open": 0, "prev_close": 0,
            "timestamp": datetime.now().isoformat(),
            "market": "MERVAL" if ".BA" in ticker else "CEDEAR",
            "ok": False,
        }

    async def get_quotes_async(self, tickers: List[str]) -> Dict[str, Dict]:
        """Cotizaciones múltiples en paralelo."""
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(None, self.get_quote, t)
            for t in tickers
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            t: (r if not isinstance(r, Exception) else self._empty_quote(t))
            for t, r in zip(tickers, results)
        }

    # ── Histórico ─────────────────────────────────────────────

    def get_history(
        self,
        ticker: str,
        days: int = 365,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Datos históricos OHLCV."""
        cache_key = f"hist:{ticker}:{days}:{interval}"
        cached = _cache.get(cache_key, ttl=300)
        if cached is not None:
            return cached

        try:
            stock = yf.Ticker(ticker)
            end = datetime.now()
            start = end - timedelta(days=days + 10)  # margen para weekends

            df = stock.history(
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                interval=interval,
                auto_adjust=True,
            )

            if df.empty:
                logger.warning(f"Sin datos históricos para {ticker}")
                return pd.DataFrame()

            df.index = pd.to_datetime(df.index)
            df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()

            _cache.set(cache_key, df)
            return df

        except Exception as e:
            logger.error(f"Error histórico {ticker}: {e}")
            return pd.DataFrame()

    # ── Scanner dinámico ────────────────────────────────────────

    def scan_opportunities(
        self,
        top_n: int = None,
        min_volume: int = 0,
    ) -> pd.DataFrame:
        """
        Escanea todo el universo y rankea los mejores activos
        según: momentum, volumen relativo, volatilidad y tendencia.

        Retorna DataFrame ordenado por score descendente.
        """
        top_n = top_n or settings.top_opportunities
        all_tickers = self.MERVAL_TICKERS + self.CEDEAR_TICKERS

        logger.info(f"🔍 Escaneando {len(all_tickers)} activos...")
        rows = []

        for ticker in all_tickers:
            try:
                df = self.get_history(ticker, days=90)
                if df.empty or len(df) < 30:
                    continue

                quote = self.get_quote(ticker)
                if not quote["ok"] or quote["price"] == 0:
                    continue

                score, metrics = self._opportunity_score(df, quote)

                rows.append({
                    "ticker":  ticker,
                    "market":  quote["market"],
                    "price":   quote["price"],
                    "change":  quote["change"],
                    "volume":  quote["volume"],
                    "score":   round(score, 3),
                    **metrics,
                })

            except Exception as e:
                logger.debug(f"Skip {ticker}: {e}")

        if not rows:
            return pd.DataFrame()

        df_scan = pd.DataFrame(rows).sort_values("score", ascending=False)
        return df_scan.head(top_n).reset_index(drop=True)

    def _opportunity_score(
        self, df: pd.DataFrame, quote: Dict
    ) -> Tuple[float, Dict]:
        """
        Calcula un score de oportunidad (0-1) basado en:
        1. Momentum  (retorno 20d normalizado)
        2. Volumen relativo (vol actual / vol promedio 20d)
        3. RSI (favorece zona 40-60, no extremos)
        4. Tendencia (precio vs SMA50)
        5. Breakout potencial (precio cerca de resistencia)
        """
        close = df["Close"]
        vol   = df["Volume"]

        # ── Momentum ──────────────────────────────────────
        ret_5d  = close.pct_change(5).iloc[-1] or 0
        ret_20d = close.pct_change(20).iloc[-1] or 0
        mom_score = np.clip((ret_20d + 0.20) / 0.40, 0, 1)   # normalizado [-20%,+20%]→[0,1]

        # ── Volumen relativo ──────────────────────────────
        avg_vol_series = vol.rolling(20).mean()
        avg_vol = avg_vol_series.dropna().iloc[-1] if not avg_vol_series.dropna().empty else 0
        avg_vol = avg_vol if avg_vol > 0 else 1
        rel_vol = quote["volume"] / avg_vol if avg_vol > 0 else 1.0
        vol_score = np.clip(rel_vol / 3.0, 0, 1)              # 3x = máximo

        # ── RSI ───────────────────────────────────────────
        delta = close.diff()
        gain  = delta.clip(lower=0).rolling(14).mean()
        loss  = (-delta.clip(upper=0)).rolling(14).mean()
        rs    = gain / loss.replace(0, np.nan)
        rsi   = (100 - 100 / (1 + rs)).iloc[-1]
        rsi   = rsi if not np.isnan(rsi) else 50

        # Score más alto en zona 35-55 (ni sobrevendido ni sobrecomprado extremo)
        if 35 <= rsi <= 55:
            rsi_score = 1.0
        elif rsi < 35:
            rsi_score = 0.5 + (35 - rsi) / 70  # oversold → oportunidad moderada
        else:
            rsi_score = max(0, 1 - (rsi - 55) / 45)

        # ── Tendencia (precio vs SMA50) ────────────────────
        sma50_series = close.rolling(50).mean()
        sma50_valid = sma50_series.dropna()
        if not sma50_valid.empty:
            sma50 = sma50_valid.iloc[-1]
        else:
            sma50 = close.rolling(min(20, len(close))).mean().iloc[-1]
        trend_score = 1.0 if close.iloc[-1] > sma50 else 0.3

        # ── Breakout: precio cerca del máximo 20d ─────────
        high20 = df["High"].rolling(20).max().iloc[-1]
        prox_high = close.iloc[-1] / high20 if high20 > 0 else 0.5
        breakout_score = np.clip(prox_high, 0, 1)

        # ── Score compuesto ponderado ──────────────────────
        weights = {
            "momentum":  0.30,
            "volume":    0.20,
            "rsi":       0.20,
            "trend":     0.20,
            "breakout":  0.10,
        }
        score = (
            weights["momentum"]  * mom_score +
            weights["volume"]    * vol_score +
            weights["rsi"]       * rsi_score +
            weights["trend"]     * trend_score +
            weights["breakout"]  * breakout_score
        )

        metrics = {
            "rsi":          round(rsi, 1),
            "ret_5d":       round(ret_5d * 100, 2),
            "ret_20d":      round(ret_20d * 100, 2),
            "rel_volume":   round(rel_vol, 2),
            "vs_sma50_pct": round((close.iloc[-1] / sma50 - 1) * 100, 2) if sma50 > 0 else 0,
            "momentum_score":  round(mom_score, 3),
            "volume_score":    round(vol_score, 3),
            "rsi_score":       round(rsi_score, 3),
            "trend_score":     round(trend_score, 3),
            "breakout_score":  round(breakout_score, 3),
        }

        return float(score), metrics


# Instancia global
data_fetcher = MarketDataFetcher()
