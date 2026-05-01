"""
strategies/signal_engine.py
Motor de señales: combina TA + ML + scanner de oportunidades.
Genera señales finales con score, razones y gestión de riesgo.
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from config.settings import settings
from config.logger import logger
from core.data_fetcher import data_fetcher
from strategies.technical import technical_analyzer, TAResult
from strategies.ml_predictor import ml_predictor, MLPrediction


@dataclass
class TradingSignal:
    """Señal de trading unificada TA + ML."""
    ticker:      str
    signal:      str           # BUY / SELL / HOLD
    score:       float         # 0-1 score final
    price:       float
    stop_loss:   float
    take_profit: float
    position_size_pct: float   # % del capital a usar
    reasons:     list = field(default_factory=list)
    ta_score:    float = 0.0
    ml_proba:    float = 0.0
    ml_signal:   str  = "HOLD"
    rsi:         float = 50.0
    timestamp:   str  = field(default_factory=lambda: datetime.now().isoformat())
    market:      str  = ""

    @property
    def is_actionable(self) -> bool:
        return (
            self.signal != "HOLD"
            and self.score >= settings.ml_min_confidence
        )

    @property
    def signal_emoji(self) -> str:
        return {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(self.signal, "⚪")

    @property
    def risk_reward(self) -> float:
        if self.price == 0:
            return 0.0
        if self.signal == "BUY":
            reward = (self.take_profit - self.price) / self.price
            risk   = (self.price - self.stop_loss) / self.price
        else:
            reward = (self.price - self.take_profit) / self.price
            risk   = (self.take_profit - self.price) / self.price

        return abs(reward / risk) if risk > 0 else 0.0


class SignalEngine:
    """
    Motor principal de señales.
    Pipeline:
    1. Obtener datos históricos
    2. Análisis técnico (score TA)
    3. Predicción ML (probabilidad)
    4. Combinar scores
    5. Calcular niveles (stop loss, take profit, tamaño)
    6. Filtrar por calidad mínima
    """

    # Pesos para combinar TA y ML
    TA_WEIGHT = 0.45
    ML_WEIGHT = 0.55

    async def analyze_ticker(self, ticker: str) -> Optional[TradingSignal]:
        """Análisis completo de un ticker."""
        try:
            # Datos históricos
            df = await asyncio.get_event_loop().run_in_executor(
                None, data_fetcher.get_history, ticker, settings.ml_lookback_days
            )

            if df.empty or len(df) < 50:
                logger.debug(f"Datos insuficientes para {ticker}")
                return None

            # Cotización actual
            quote = await asyncio.get_event_loop().run_in_executor(
                None, data_fetcher.get_quote, ticker
            )
            price = quote.get("price", 0)
            if price == 0:
                return None

            # Análisis técnico
            ta: TAResult = technical_analyzer.analyze(df, ticker)

            # ML: reentrenar si es necesario
            if ml_predictor.needs_retraining(ticker):
                await asyncio.get_event_loop().run_in_executor(
                    None, ml_predictor.train, df, ticker
                )
            ml: MLPrediction = await asyncio.get_event_loop().run_in_executor(
                None, ml_predictor.predict, df, ticker
            )

            # ── Combinar scores ─────────────────────────────────
            # TA score: [-1, 1] → [0, 1]
            ta_normalized = (ta.ta_score + 1) / 2

            # ML: probabilidad de la señal
            ml_normalized = ml.probability if ml.signal != "HOLD" else 0.5

            combined_score = (
                self.TA_WEIGHT * ta_normalized +
                self.ML_WEIGHT * ml_normalized
            )

            # Determinar señal final
            ta_buy  = ta.signal == "BUY"
            ta_sell = ta.signal == "SELL"
            ml_buy  = ml.signal == "BUY"
            ml_sell = ml.signal == "SELL"

            # Consenso: ambos deben estar de acuerdo O uno muy fuerte
            if ta_buy and ml_buy:
                final_signal = "BUY"
            elif ta_sell and ml_sell:
                final_signal = "SELL"
            elif ta_buy and ml.probability < 0.45:
                final_signal = "HOLD"
            elif ta_sell and ml.probability < 0.45:
                final_signal = "HOLD"
            elif ml_buy and ta.ta_score > 0.2:
                final_signal = "BUY"
            elif ml_sell and ta.ta_score < -0.2:
                final_signal = "SELL"
            else:
                final_signal = "HOLD"

            # Score final ajustado por consenso
            if final_signal == "HOLD":
                combined_score = min(combined_score, 0.55)

            # ── Niveles de precio ───────────────────────────────
            atr = df["High"].sub(df["Low"]).rolling(14).mean().iloc[-1]
            atr_pct = atr / price if price > 0 else 0.02

            sl_pct = max(settings.stop_loss_pct, atr_pct * 1.5)
            tp_pct = settings.take_profit_pct

            if final_signal == "BUY":
                stop_loss   = round(price * (1 - sl_pct), 2)
                take_profit = round(price * (1 + tp_pct), 2)
            elif final_signal == "SELL":
                stop_loss   = round(price * (1 + sl_pct), 2)
                take_profit = round(price * (1 - tp_pct), 2)
            else:
                stop_loss   = round(price * (1 - sl_pct), 2)
                take_profit = round(price * (1 + tp_pct), 2)

            # ── Tamaño de posición (Kelly fraccionario) ─────────
            win_prob  = ml.probability
            loss_prob = 1 - win_prob
            edge = win_prob * tp_pct - loss_prob * sl_pct
            kelly = edge / tp_pct if tp_pct > 0 else 0
            kelly_fraction = max(0, min(kelly * 0.5, settings.max_position_size_pct))
            # Usar mínimo entre Kelly y límite configurado
            position_pct = round(min(kelly_fraction, settings.max_position_size_pct), 4)

            # Razones combinadas
            reasons = ta.reasons.copy()
            if ml.signal != "HOLD":
                reasons.append(f"ML: {ml.signal} ({ml.probability:.0%} conf.)")
            if ml.model_accuracy > 0:
                reasons.append(f"Accuracy histórica: {ml.model_accuracy:.0%}")

            return TradingSignal(
                ticker=ticker,
                signal=final_signal,
                score=round(combined_score, 4),
                price=price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size_pct=position_pct,
                reasons=reasons[:8],
                ta_score=ta.ta_score,
                ml_proba=ml.probability,
                ml_signal=ml.signal,
                rsi=ta.indicators.get("rsi", 50),
                market=quote.get("market", ""),
            )

        except Exception as e:
            logger.error(f"Error analizando {ticker}: {e}")
            return None

    async def scan_and_rank(self) -> List[TradingSignal]:
        """
        Escanea las mejores oportunidades del momento y las rankea.
        1. Usa el scanner de data_fetcher para preseleccionar top N por score técnico rápido
        2. Aplica análisis TA + ML completo sobre el top
        """
        logger.info("🔍 Iniciando scan de mercado...")

        # Preselección rápida
        scan_df = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: data_fetcher.scan_opportunities(top_n=settings.top_opportunities + 5)
        )

        if scan_df.empty:
            logger.warning("Scanner no encontró activos")
            return []

        tickers = scan_df["ticker"].tolist()
        logger.info(f"📋 Analizando {len(tickers)} activos seleccionados...")

        # Análisis completo en paralelo (con límite de concurrencia)
        semaphore = asyncio.Semaphore(5)

        async def analyze_with_sem(ticker):
            async with semaphore:
                return await self.analyze_ticker(ticker)

        tasks = [analyze_with_sem(t) for t in tickers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        signals = []
        for r in results:
            if isinstance(r, TradingSignal) and r is not None:
                signals.append(r)

        # Rankear: primero accionables, luego por score
        signals.sort(key=lambda s: (
            s.signal != "HOLD",
            s.score,
        ), reverse=True)

        actionable = [s for s in signals if s.is_actionable]
        rest       = [s for s in signals if not s.is_actionable]

        logger.info(
            f"✅ Análisis completo: {len(signals)} activos | "
            f"{len(actionable)} señales accionables"
        )

        return (actionable + rest)[:settings.top_opportunities]

    async def analyze_specific(self, tickers: List[str]) -> List[TradingSignal]:
        """Analiza una lista específica de tickers."""
        tasks = [self.analyze_ticker(t) for t in tickers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, TradingSignal) and r is not None]


# Instancia global
signal_engine = SignalEngine()
