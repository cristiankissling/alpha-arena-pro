"""
telegram/bot.py
Bot de Telegram con comandos reales implementados.
"""
import asyncio
from datetime import datetime
from typing import Optional, List
import pandas as pd

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application, CommandHandler, CallbackQueryHandler,
        MessageHandler, filters, ContextTypes,
    )
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

from config.settings import settings
from config.logger import logger


class TelegramNotifier:
    """
    Bot de Telegram.
    Si no hay token configurado, actúa como notificador silencioso.
    """

    def __init__(self):
        self.app: Optional[object] = None
        self._is_running = False

    async def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Enviar mensaje al chat configurado."""
        if not settings.telegram_token or not settings.telegram_chat_id:
            return False
        if not TELEGRAM_AVAILABLE:
            logger.debug(f"[Telegram simulado] {text[:100]}")
            return True

        try:
            if self.app:
                await self.app.bot.send_message(
                    chat_id=settings.telegram_chat_id,
                    text=text,
                    parse_mode=parse_mode,
                    disable_web_page_preview=True,
                )
                return True
        except Exception as e:
            logger.error(f"Error enviando Telegram: {e}")
        return False

    async def send_signal_alert(self, signal) -> bool:
        """Enviar alerta de señal de trading."""
        emoji = signal.signal_emoji
        msg = (
            f"{emoji} *SEÑAL: {signal.signal}* — `{signal.ticker}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 Precio: `${signal.price:,.2f}`\n"
            f"🎯 Score: `{signal.score:.0%}`\n"
            f"🤖 ML: `{signal.ml_proba:.0%}` ({signal.ml_signal})\n"
            f"📊 TA Score: `{signal.ta_score:+.2f}`\n"
            f"📉 Stop Loss: `${signal.stop_loss:,.2f}`\n"
            f"📈 Take Profit: `${signal.take_profit:,.2f}`\n"
            f"⚖️ R/R: `{signal.risk_reward:.1f}x`\n"
            f"📦 Posición: `{signal.position_size_pct:.0%}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 *Razones:*\n"
        )
        for r in signal.reasons[:4]:
            msg += f"• {r}\n"
        msg += f"\n_⏰ {datetime.now().strftime('%H:%M:%S')}_"
        return await self.send_message(msg)

    async def send_daily_summary(self, signals: list, stats: dict) -> bool:
        """Resumen diario."""
        buy_signals  = [s for s in signals if s.signal == "BUY"]
        sell_signals = [s for s in signals if s.signal == "SELL"]

        msg = (
            f"📊 *RESUMEN DIARIO — Alpha Arena Pro*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
            f"🟢 Señales BUY: {len(buy_signals)}\n"
            f"🔴 Señales SELL: {len(sell_signals)}\n\n"
        )

        if buy_signals:
            msg += "*Top BUY:*\n"
            for s in buy_signals[:3]:
                msg += f"• `{s.ticker}` — Score: {s.score:.0%} | ${s.price:,.2f}\n"
            msg += "\n"

        if sell_signals:
            msg += "*Top SELL:*\n"
            for s in sell_signals[:3]:
                msg += f"• `{s.ticker}` — Score: {s.score:.0%} | ${s.price:,.2f}\n"
            msg += "\n"

        msg += (
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📈 P&L Total: `${stats.get('total_pnl', 0):,.2f}`\n"
            f"🏆 Win Rate: `{stats.get('win_rate', 0):.1%}`\n"
            f"🔄 Trades: `{stats.get('total_trades', 0)}`\n"
        )

        return await self.send_message(msg)

    async def send_risk_alert(self, message: str) -> bool:
        """Alerta de riesgo urgente."""
        msg = f"⚠️ *ALERTA DE RIESGO*\n━━━━━━━━━━━━━\n{message}\n_⏰ {datetime.now().strftime('%H:%M:%S')}_"
        return await self.send_message(msg)

    def start_polling(self):
        """Iniciar bot en modo polling (bloquea el hilo)."""
        if not TELEGRAM_AVAILABLE or not settings.telegram_token:
            logger.info("Telegram no configurado, modo silencioso.")
            return

        from telegram.ext import Application, CommandHandler

        self.app = Application.builder().token(settings.telegram_token).build()

        # Handlers básicos
        self.app.add_handler(CommandHandler("start",  self._cmd_start))
        self.app.add_handler(CommandHandler("status", self._cmd_status))
        self.app.add_handler(CommandHandler("help",   self._cmd_help))

        logger.info("🤖 Bot Telegram iniciado en polling")
        self.app.run_polling(allowed_updates=["message"])

    # ── Command handlers ─────────────────────────────────────

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤖 *Alpha Arena Pro*\n\nUsa /help para ver los comandos.",
            parse_mode="Markdown",
        )

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            f"✅ Bot activo\n⏰ {datetime.now().strftime('%H:%M:%S')}",
            parse_mode="Markdown",
        )

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "*Comandos disponibles:*\n"
            "/start — Bienvenida\n"
            "/status — Estado del bot\n"
            "/help — Esta ayuda\n",
            parse_mode="Markdown",
        )


# Instancia global
telegram_bot = TelegramNotifier()
