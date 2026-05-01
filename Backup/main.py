#!/usr/bin/env python3
"""
main.py
Punto de entrada principal de Alpha Arena Pro.
Ejecuta el motor de trading y lanza el dashboard en paralelo.

Uso:
    python main.py              → bot completo + dashboard
    python main.py --bot-only   → solo el motor de trading
    python main.py --dash-only  → solo el dashboard
    python main.py --scan       → un scan único y salir
    python main.py --backtest GGAL.BA → backtest rápido
"""
import asyncio
import sys
import os
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import settings
from config.logger import logger


def print_banner():
    banner = f"""
╔══════════════════════════════════════════════════════════╗
║          🚀 ALPHA ARENA PRO — Trading Bot v{settings.version}         ║
║                Mercado Argentino + CEDEARs               ║
╚══════════════════════════════════════════════════════════╝

  Modo:        {settings.trading_mode.upper()}
  Capital:     ${settings.initial_capital:,.0f}
  Universo:    {len(settings.all_tickers)} activos
  ML Conf.:    {settings.ml_min_confidence:.0%}
  Dashboard:   http://localhost:{settings.dashboard_port}
  Ambiente:    {settings.environment}
  ─────────────────────────────────────────────────────────
"""
    print(banner)


def launch_dashboard():
    """Lanzar dashboard Streamlit como proceso separado."""
    dashboard_path = Path(__file__).parent / "dashboard" / "app.py"
    logger.info(f"🖥️  Lanzando dashboard en http://localhost:{settings.dashboard_port}")
    return subprocess.Popen([
        sys.executable, "-m", "streamlit", "run",
        str(dashboard_path),
        "--server.port", str(settings.dashboard_port),
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
    ])


async def run_single_scan():
    """Ejecutar un scan único y mostrar resultados."""
    from core.data_fetcher import data_fetcher

    print("\n🔍 Ejecutando scan de mercado...\n")
    scan_df = data_fetcher.scan_opportunities(top_n=10)

    if scan_df.empty:
        print("❌ No se encontraron resultados.")
        return

    print(f"{'#':<3} {'Ticker':<12} {'Mercado':<10} {'Precio':>10} {'Cambio':>8} {'Score':>7} {'RSI':>6} {'Ret20d':>8}")
    print("─" * 75)

    for i, (_, row) in enumerate(scan_df.iterrows(), 1):
        signal = "🟢" if row["rsi"] < 45 else ("🔴" if row["rsi"] > 65 else "🟡")
        print(
            f"{i:<3} {row['ticker']:<12} {row['market']:<10} "
            f"${row['price']:>9,.2f} {row['change']:>+7.2f}% "
            f"{row['score']:>6.0%} {row['rsi']:>6.1f} {row['ret_20d']:>+7.1f}%  {signal}"
        )

    print(f"\n✅ Scan completado: {len(scan_df)} activos")


async def run_quick_backtest(ticker: str):
    """Backtest rápido por línea de comando."""
    from core.data_fetcher import data_fetcher
    from strategies.backtester import backtester

    print(f"\n📊 Ejecutando backtest para {ticker}...\n")

    df = data_fetcher.get_history(ticker, 365)
    if df.empty:
        print(f"❌ Sin datos para {ticker}")
        return

    try:
        result = backtester.run(df, ticker=ticker, strategy="technical")
        summary = result.summary_dict()

        print("═" * 45)
        for k, v in summary.items():
            print(f"  {k:<20} {v}")
        print("═" * 45)

    except Exception as e:
        print(f"❌ Error en backtest: {e}")


async def main():
    """Función principal async."""
    parser = argparse.ArgumentParser(description="Alpha Arena Pro")
    parser.add_argument("--bot-only",  action="store_true", help="Solo motor de trading")
    parser.add_argument("--dash-only", action="store_true", help="Solo dashboard")
    parser.add_argument("--scan",      action="store_true", help="Scan único y salir")
    parser.add_argument("--backtest",  type=str, metavar="TICKER", help="Backtest rápido")
    args = parser.parse_args()

    print_banner()

    # Crear directorios necesarios
    settings.data_dir.mkdir(exist_ok=True)
    settings.logs_dir.mkdir(exist_ok=True)
    settings.models_dir.mkdir(exist_ok=True)

    # Inicializar BD
    from core.database import db
    await db.initialize()

    # ── Modos especiales ─────────────────────────────────────
    if args.scan:
        await run_single_scan()
        return

    if args.backtest:
        await run_quick_backtest(args.backtest)
        return

    # ── Dashboard ─────────────────────────────────────────────
    dash_process = None
    if not args.bot_only:
        dash_process = launch_dashboard()

    # ── Bot de trading ─────────────────────────────────────────
    if not args.dash_only:
        from core.trading_bot import trading_bot
        try:
            logger.info("🤖 Iniciando motor de trading...")
            await trading_bot.run()
        except KeyboardInterrupt:
            logger.info("🛑 Bot detenido por el usuario")
        finally:
            if dash_process:
                dash_process.terminate()
    else:
        # Solo dashboard: esperar
        print(f"\n✅ Dashboard corriendo en http://localhost:{settings.dashboard_port}")
        print("   Presiona Ctrl+C para detener\n")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            if dash_process:
                dash_process.terminate()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Alpha Arena Pro detenido")
