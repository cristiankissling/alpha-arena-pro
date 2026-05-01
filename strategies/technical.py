"""
strategies/technical.py
Análisis técnico completo: RSI, MACD, Bollinger, EMA, ATR, ADX, Stochastic, VWAP.
Genera un score técnico compuesto y señales claras.
"""
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class TAResult:
    """Resultado completo del análisis técnico."""
    ticker: str
    signal: str           # BUY / SELL / HOLD
    ta_score: float       # -1.0 (fuerte venta) a +1.0 (fuerte compra)
    confidence: float     # 0-1
    reasons: list = field(default_factory=list)
    indicators: dict = field(default_factory=dict)

    @property
    def is_buy(self) -> bool:
        return self.signal == "BUY"

    @property
    def is_sell(self) -> bool:
        return self.signal == "SELL"

    @property
    def signal_emoji(self) -> str:
        return {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(self.signal, "⚪")


class TechnicalAnalyzer:
    """
    Motor de análisis técnico multi-indicador.
    Cada indicador vota (+1 compra, -1 venta, 0 neutral).
    El score final es el promedio ponderado de votos.
    """

    def analyze(self, df: pd.DataFrame, ticker: str = "") -> TAResult:
        """Análisis completo sobre un DataFrame OHLCV."""
        if df.empty or len(df) < 50:
            return TAResult(ticker=ticker, signal="HOLD", ta_score=0.0, confidence=0.0,
                           reasons=["Datos insuficientes"])

        df = df.copy()
        votes = {}
        reasons = []
        indicators = {}

        # ── Calcular todos los indicadores ────────────────────────
        df = self._add_all_indicators(df)

        row = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else row

        # ── 1. RSI ─────────────────────────────────────────────────
        rsi = row.get("rsi", 50)
        indicators["rsi"] = round(rsi, 1)
        if rsi < 30:
            votes["rsi"] = 1.0
            reasons.append(f"RSI={rsi:.0f} (sobreventa)")
        elif rsi < 40:
            votes["rsi"] = 0.5
            reasons.append(f"RSI={rsi:.0f} (zona baja)")
        elif rsi > 70:
            votes["rsi"] = -1.0
            reasons.append(f"RSI={rsi:.0f} (sobrecompra)")
        elif rsi > 60:
            votes["rsi"] = -0.5
            reasons.append(f"RSI={rsi:.0f} (zona alta)")
        else:
            votes["rsi"] = 0.0

        # ── 2. MACD ────────────────────────────────────────────────
        macd_val = row.get("macd", 0)
        macd_sig = row.get("macd_signal", 0)
        macd_hist = row.get("macd_hist", 0)
        prev_hist = prev.get("macd_hist", 0)
        indicators["macd"] = round(macd_val, 4)
        indicators["macd_signal"] = round(macd_sig, 4)
        indicators["macd_hist"] = round(macd_hist, 4)

        if macd_hist > 0 and prev_hist <= 0:
            votes["macd"] = 1.0
            reasons.append("MACD cruce alcista")
        elif macd_hist < 0 and prev_hist >= 0:
            votes["macd"] = -1.0
            reasons.append("MACD cruce bajista")
        elif macd_hist > 0:
            votes["macd"] = 0.5
        else:
            votes["macd"] = -0.5

        # ── 3. Bollinger Bands ─────────────────────────────────────
        bb_upper = row.get("bb_upper", 0)
        bb_lower = row.get("bb_lower", 0)
        bb_mid   = row.get("bb_mid", 0)
        close    = row["Close"]
        indicators["bb_upper"] = round(bb_upper, 2)
        indicators["bb_lower"] = round(bb_lower, 2)
        indicators["bb_pct"] = round(
            (close - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5, 3
        )

        if close < bb_lower:
            votes["bb"] = 1.0
            reasons.append("Precio bajo banda BB inferior")
        elif close > bb_upper:
            votes["bb"] = -1.0
            reasons.append("Precio sobre banda BB superior")
        elif close < bb_mid:
            votes["bb"] = 0.3
        else:
            votes["bb"] = -0.3

        # ── 4. EMA Crossover ───────────────────────────────────────
        ema20 = row.get("ema20", close)
        ema50 = row.get("ema50", close)
        ema200 = row.get("ema200", close)
        indicators["ema20"] = round(ema20, 2)
        indicators["ema50"] = round(ema50, 2)
        indicators["ema200"] = round(ema200, 2)

        prev_ema20 = prev.get("ema20", ema20)
        prev_ema50 = prev.get("ema50", ema50)

        if ema20 > ema50 and prev_ema20 <= prev_ema50:
            votes["ema_cross"] = 1.0
            reasons.append("Golden cross EMA20/50")
        elif ema20 < ema50 and prev_ema20 >= prev_ema50:
            votes["ema_cross"] = -1.0
            reasons.append("Death cross EMA20/50")
        elif ema20 > ema50:
            votes["ema_cross"] = 0.4
        else:
            votes["ema_cross"] = -0.4

        # ── 5. Tendencia de largo plazo (vs EMA200) ────────────────
        if close > ema200 * 1.02:
            votes["trend"] = 0.5
        elif close < ema200 * 0.98:
            votes["trend"] = -0.5
            reasons.append("Precio bajo EMA200 (tendencia bajista)")
        else:
            votes["trend"] = 0.0

        # ── 6. Stochastic ──────────────────────────────────────────
        stoch_k = row.get("stoch_k", 50)
        stoch_d = row.get("stoch_d", 50)
        indicators["stoch_k"] = round(stoch_k, 1)
        indicators["stoch_d"] = round(stoch_d, 1)

        if stoch_k < 20 and stoch_k > stoch_d:
            votes["stoch"] = 1.0
            reasons.append(f"Stoch oversold + cruce ({stoch_k:.0f})")
        elif stoch_k > 80 and stoch_k < stoch_d:
            votes["stoch"] = -1.0
            reasons.append(f"Stoch overbought + cruce ({stoch_k:.0f})")
        elif stoch_k < 20:
            votes["stoch"] = 0.5
        elif stoch_k > 80:
            votes["stoch"] = -0.5
        else:
            votes["stoch"] = 0.0

        # ── 7. ADX (fuerza de tendencia) ───────────────────────────
        adx = row.get("adx", 20)
        di_plus = row.get("di_plus", 25)
        di_minus = row.get("di_minus", 25)
        indicators["adx"] = round(adx, 1)

        if adx > 25:
            # Tendencia fuerte: amplificar la señal direccional
            if di_plus > di_minus:
                votes["adx"] = 0.5
            else:
                votes["adx"] = -0.5
        else:
            votes["adx"] = 0.0

        # ── 8. Volumen ─────────────────────────────────────────────
        avg_vol = df["Volume"].rolling(20).mean().iloc[-1] or 1
        curr_vol = row.get("Volume", avg_vol)
        rel_vol = curr_vol / avg_vol
        indicators["volume_ratio"] = round(rel_vol, 2)

        if rel_vol > 1.5:
            # Volumen alto confirma el movimiento
            votes["volume"] = 0.3 if close > prev["Close"] else -0.3
        else:
            votes["volume"] = 0.0

        # ── Score final ponderado ──────────────────────────────────
        weights = {
            "rsi":       1.5,
            "macd":      2.0,
            "bb":        1.5,
            "ema_cross": 2.0,
            "trend":     1.0,
            "stoch":     1.0,
            "adx":       1.0,
            "volume":    0.5,
        }

        total_weight = sum(weights.values())
        weighted_score = sum(
            votes.get(k, 0) * w for k, w in weights.items()
        ) / total_weight

        # Señal y confianza
        if weighted_score >= 0.35:
            signal = "BUY"
        elif weighted_score <= -0.35:
            signal = "SELL"
        else:
            signal = "HOLD"

        confidence = min(abs(weighted_score) * 2, 1.0)  # 0.35 → 0.70, 0.50 → 1.0

        # Soporte / resistencia simples
        high20 = df["High"].rolling(20).max().iloc[-1]
        low20  = df["Low"].rolling(20).min().iloc[-1]
        indicators["resistance_20d"] = round(high20, 2)
        indicators["support_20d"]    = round(low20, 2)
        indicators["close"] = round(close, 2)

        return TAResult(
            ticker=ticker,
            signal=signal,
            ta_score=round(weighted_score, 4),
            confidence=round(confidence, 4),
            reasons=reasons[:6],     # top 6 razones
            indicators=indicators,
        )

    # ── Cálculo de indicadores ─────────────────────────────────

    def _add_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        close = df["Close"]
        high  = df["High"]
        low   = df["Low"]
        vol   = df["Volume"]

        # RSI
        delta = close.diff()
        gain  = delta.clip(lower=0).rolling(14).mean()
        loss  = (-delta.clip(upper=0)).rolling(14).mean()
        rs    = gain / loss.replace(0, np.nan)
        df["rsi"] = 100 - 100 / (1 + rs)

        # MACD
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        df["macd"]        = ema12 - ema26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_hist"]   = df["macd"] - df["macd_signal"]

        # Bollinger Bands
        sma20      = close.rolling(20).mean()
        std20      = close.rolling(20).std()
        df["bb_mid"]   = sma20
        df["bb_upper"] = sma20 + 2 * std20
        df["bb_lower"] = sma20 - 2 * std20

        # EMAs
        df["ema20"]  = close.ewm(span=20,  adjust=False).mean()
        df["ema50"]  = close.ewm(span=50,  adjust=False).mean()
        df["ema200"] = close.ewm(span=200, adjust=False).mean()

        # Stochastic
        low14  = low.rolling(14).min()
        high14 = high.rolling(14).max()
        df["stoch_k"] = 100 * (close - low14) / (high14 - low14).replace(0, np.nan)
        df["stoch_d"] = df["stoch_k"].rolling(3).mean()

        # ATR
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low  - close.shift()).abs(),
        ], axis=1).max(axis=1)
        df["atr"] = tr.rolling(14).mean()

        # ADX
        df["di_plus"]  = 100 * (high.diff().clip(lower=0) / df["atr"].replace(0, np.nan)).rolling(14).mean()
        df["di_minus"] = 100 * ((-low.diff()).clip(lower=0) / df["atr"].replace(0, np.nan)).rolling(14).mean()
        dx = 100 * (df["di_plus"] - df["di_minus"]).abs() / (df["di_plus"] + df["di_minus"]).replace(0, np.nan)
        df["adx"] = dx.rolling(14).mean()

        return df

    # ── Helpers estáticos ──────────────────────────────────────

    @staticmethod
    def get_indicators_df(df: pd.DataFrame) -> pd.DataFrame:
        """Retorna DataFrame con todos los indicadores calculados (para gráficos)."""
        analyzer = TechnicalAnalyzer()
        return analyzer._add_all_indicators(df.copy())


# Instancia global
technical_analyzer = TechnicalAnalyzer()
