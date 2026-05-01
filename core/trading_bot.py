"""
core/trading_bot.py
Orquestador principal del bot de trading.
Ciclo de análisis → señales → alertas → base de datos.
"""
import asyncio
from datetime import datetime, time as dtime
from typing import List, Optional, Dict
import pytz

from config.settings import settings
from config.logger import logger
from core.database import db
from core.data_fetcher import data_fetcher
from strategies.signal_engine import signal_engine, TradingSignal
from telegram.bot import telegram_bot


# Zona horaria argentina
AR_TZ = pytz.timezone("America/Argentina/Buenos_Aires")

# Horario MERVAL y CEDEARs
MARKET_OPEN_MERVAL  = dtime(11, 00)
MARKET_CLOSE_MERVAL = dtime(17, 30)
MARKET_OPEN_US      = dtime(10, 30)   # horario apertura NY en AR
MARKET_CLOSE_US     = dtime(17, 00)


class TradingBot:
    """
    Bot de trading principal.
    - Ciclo periódico de análisis
    - Gestión de señales y trades
    - Alertas Telegram
    - Persistencia en base de datos
    """

    def __init__(self):
        self.is_running     = False
        self.cycle_count    = 0
        self.start_time     = None
        self.last_signals:  List[TradingSignal] = []
        self.status         = "STOPPED"
        self.open_positions: Dict[str, TradingSignal] = {}
        self._paper_trades: List[Dict] = []   # simulación paper trading

    # ── Ciclo principal ────────────────────────────────────────

    async def run(self):
        """Bucle principal del bot."""
        logger.info("🚀 Iniciando Alpha Arena Pro...")
        self.is_running  = True
        self.status      = "RUNNING"
        self.start_time  = datetime.now()

        # Inicializar base de datos
        await db.initialize()

        # Notificación de inicio
        await telegram_bot.send_message(
            f"🚀 *Alpha Arena Pro iniciado*\n"
            f"Modo: `{settings.trading_mode.upper()}`\n"
            f"Capital: `${settings.initial_capital:,.0f}`\n"
            f"Universo: `{len(settings.all_tickers)}` activos\n"
            f"⏰ {datetime.now().strftime('%H:%M:%S')}"
        )

        try:
            while self.is_running:
                self.cycle_count += 1
                logger.info(f"🔄 Ciclo #{self.cycle_count}")

                await self._analysis_cycle()
                await asyncio.sleep(settings.analysis_interval_seconds)

        except asyncio.CancelledError:
            logger.info("Bot detenido correctamente")
        except Exception as e:
            logger.error(f"Error en ciclo principal: {e}", exc_info=True)
            await telegram_bot.send_risk_alert(f"Error en bot: {e}")
        finally:
            self.is_running = False
            self.status     = "STOPPED"

    async def _analysis_cycle(self):
        """Un ciclo completo de análisis."""
        try:
            now_ar = datetime.now(AR_TZ)
            logger.info(f"⏰ {now_ar.strftime('%H:%M:%S')} AR | Escaneando mercado...")

            # Escanear y generar señales
            signals = await signal_engine.scan_and_rank()
            self.last_signals = signals

            # Guardar señales en BD
            for sig in signals:
                await db.save_signal({
                    "ticker":     sig.ticker,
                    "signal_type": sig.signal,
                    "score":      sig.score,
                    "price":      sig.price,
                    "reason":     " | ".join(sig.reasons),
                    "indicators": {
                        "rsi":    sig.rsi,
                        "ta_score": sig.ta_score,
                    },
                    "ml_proba":  sig.ml_proba,
                    "ta_score":  sig.ta_score,
                })

            # Señales accionables
            actionable = [s for s in signals if s.is_actionable]

            if actionable:
                logger.info(f"🎯 {len(actionable)} señales accionables")

                for sig in actionable[:3]:   # máximo 3 alertas por ciclo
                    logger.info(
                        f"{sig.signal_emoji} {sig.ticker} | "
                        f"Score: {sig.score:.0%} | "
                        f"${sig.price:,.2f}"
                    )

                    # Alerta Telegram
                    if settings.enable_telegram_alerts:
                        await telegram_bot.send_signal_alert(sig)

                    # Paper trading
                    if settings.trading_mode == "paper":
                        await self._execute_paper_trade(sig)

            # Verificar posiciones abiertas
            await self._check_open_positions(signals)

            # Guardar snapshot de mercado para los top activos
            for sig in signals[:5]:
                await db.save_snapshot({
                    "ticker":     sig.ticker,
                    "price":      sig.price,
                    "change_pct": 0,
                    "volume":     0,
                    "high":       0,
                    "low":        0,
                    "market":     sig.market,
                })

        except Exception as e:
            logger.error(f"Error en ciclo de análisis: {e}", exc_info=True)

    async def _execute_paper_trade(self, signal: TradingSignal):
        """Ejecutar trade simulado (paper trading)."""
        # Verificar si ya tenemos posición en este ticker
        if signal.ticker in self.open_positions:
            return

        # Verificar límite de posiciones abiertas
        if len(self.open_positions) >= settings.max_open_positions:
            logger.info(f"Máximo de posiciones abiertas alcanzado ({settings.max_open_positions})")
            return

        # Registrar trade en BD
        trade_data = {
            "ticker":     signal.ticker,
            "side":       signal.signal,
            "quantity":   int(settings.initial_capital * signal.position_size_pct / signal.price) if signal.price > 0 else 0,
            "entry_price": signal.price,
            "stop_loss":  signal.stop_loss,
            "take_profit": signal.take_profit,
            "signal_score": signal.score,
            "strategy":   "signal_engine_v2",
            "trade_meta": {
                "ta_score":  signal.ta_score,
                "ml_proba":  signal.ml_proba,
                "reasons":   signal.reasons,
            },
        }

        if trade_data["quantity"] > 0:
            trade = await db.save_trade(trade_data)
            self.open_positions[signal.ticker] = signal
            logger.info(
                f"📝 Paper trade abierto: {signal.signal} {signal.ticker} "
                f"× {trade_data['quantity']} @ ${signal.price:.2f}"
            )

    async def _check_open_positions(self, current_signals: List[TradingSignal]):
        """Verificar si alguna posición abierta debe cerrarse."""
        open_trades = await db.get_open_trades()

        # Obtener cotizaciones actuales
        tickers = list({t.ticker for t in open_trades})
        if not tickers:
            return

        quotes = await data_fetcher.get_quotes_async(tickers)

        for trade in open_trades:
            quote = quotes.get(trade.ticker, {})
            current_price = quote.get("price", 0)
            if current_price == 0:
                continue

            should_close = False
            reason = ""

            # Check stop loss
            if trade.side == "BUY" and trade.stop_loss and current_price <= trade.stop_loss:
                should_close = True
                reason = "Stop Loss alcanzado"
            elif trade.side == "SELL" and trade.stop_loss and current_price >= trade.stop_loss:
                should_close = True
                reason = "Stop Loss alcanzado"

            # Check take profit
            if trade.side == "BUY" and trade.take_profit and current_price >= trade.take_profit:
                should_close = True
                reason = "Take Profit alcanzado 🎯"
            elif trade.side == "SELL" and trade.take_profit and current_price <= trade.take_profit:
                should_close = True
                reason = "Take Profit alcanzado 🎯"

            if should_close:
                pnl = 0
                if trade.side == "BUY":
                    pnl = (current_price - trade.entry_price) * trade.quantity
                else:
                    pnl = (trade.entry_price - current_price) * trade.quantity

                pnl_pct = (pnl / (trade.entry_price * trade.quantity)) * 100

                await db.close_trade(trade.id, current_price, pnl, pnl_pct)

                if trade.ticker in self.open_positions:
                    del self.open_positions[trade.ticker]

                logger.info(f"✅ Trade cerrado: {trade.ticker} | P&L: ${pnl:,.2f} | {reason}")

                if settings.enable_telegram_alerts:
                    emoji = "🟢" if pnl > 0 else "🔴"
                    await telegram_bot.send_message(
                        f"{emoji} *Trade Cerrado: {trade.ticker}*\n"
                        f"Razón: {reason}\n"
                        f"P&L: `${pnl:,.2f}` ({pnl_pct:+.2f}%)\n"
                        f"Precio: `${current_price:,.2f}`"
                    )

    # ── Métodos de control ─────────────────────────────────────

    def stop(self):
        self.is_running = False
        self.status = "STOPPED"
        logger.info("🛑 Bot detenido")

    @property
    def uptime(self) -> str:
        if not self.start_time:
            return "00:00:00"
        delta = datetime.now() - self.start_time
        h, rem = divmod(int(delta.total_seconds()), 3600)
        m, s   = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def get_status(self) -> Dict:
        return {
            "status":       self.status,
            "is_running":   self.is_running,
            "cycle_count":  self.cycle_count,
            "uptime":       self.uptime,
            "mode":         settings.trading_mode,
            "open_positions": len(self.open_positions),
            "last_scan":    datetime.now().isoformat(),
            "signals_count": len(self.last_signals),
        }


# Instancia global
trading_bot = TradingBot()
