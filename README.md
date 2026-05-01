# 🚀 Alpha Arena Pro — Trading Bot MERVAL + CEDEARs

Bot de trading con análisis técnico avanzado + Machine Learning para el mercado argentino.

## ✨ Características

- **Scanner dinámico**: Detecta las mejores oportunidades del MERVAL y CEDEARs automáticamente
- **Análisis técnico completo**: RSI, MACD, Bollinger Bands, EMAs (20/50/200), Stochastic, ADX, ATR
- **ML con XGBoost**: 30+ features, time-series CV, reentrenamiento automático
- **Señales combinadas**: TA + ML con scoring ponderado y gestión de riesgo
- **Dashboard Streamlit**: 6 páginas con gráficos interactivos
- **Paper Trading**: Simulación completa con BD SQLite
- **Telegram**: Alertas de señales en tiempo real (opcional)
- **Backtesting**: 3 estrategias con métricas profesionales (Sharpe, Sortino, Calmar, Drawdown)

## 🏗️ Estructura

```
trading_bot/
├── main.py                 ← Punto de entrada
├── config/
│   ├── settings.py         ← Configuración central
│   └── logger.py           ← Logging
├── core/
│   ├── data_fetcher.py     ← Datos de mercado + scanner
│   ├── database.py         ← SQLite async (SQLAlchemy)
│   └── trading_bot.py      ← Orquestador principal
├── strategies/
│   ├── technical.py        ← Motor TA (8 indicadores)
│   ├── ml_predictor.py     ← XGBoost + feature engineering
│   ├── signal_engine.py    ← Señales combinadas TA+ML
│   └── backtester.py       ← Motor de backtesting
├── dashboard/
│   └── app.py              ← Dashboard Streamlit (6 páginas)
├── telegram/
│   └── bot.py              ← Bot de Telegram
├── data/                   ← BD y modelos ML (auto-creado)
├── logs/                   ← Logs diarios (auto-creado)
├── .env.example            ← Template de configuración
└── requirements.txt
```

## ⚡ Instalación rápida

```bash
# 1. Crear entorno virtual
python -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate    # Windows

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tu configuración

# 4. Lanzar todo integrado
python main.py
```

## 🎯 Modos de uso

```bash
# Bot completo + dashboard (recomendado)
python main.py

# Solo dashboard
python main.py --dash-only

# Solo bot de trading
python main.py --bot-only

# Scan rápido de oportunidades
python main.py --scan

# Backtest rápido
python main.py --backtest GGAL.BA
python main.py --backtest AAPL
```

## 📊 Dashboard

Acceder en `http://localhost:8501`

| Página | Descripción |
|--------|-------------|
| 🏠 Dashboard | Cotizaciones MERVAL + CEDEARs en tiempo real |
| 🔍 Scanner | Ranking dinámico de oportunidades |
| 📊 Análisis | Análisis técnico con gráficos interactivos |
| 🤖 ML Predictor | Predicciones XGBoost por ticker |
| ⚡ Backtest | Test de estrategias con métricas pro |
| 📈 Portfolio | Posiciones abiertas e historial |

## 🔔 Telegram (opcional)

1. Crear un bot en [@BotFather](https://t.me/BotFather)
2. Agregar en `.env`:
   ```
   TELEGRAM_TOKEN=tu_token
   TELEGRAM_CHAT_ID=tu_chat_id
   ENABLE_TELEGRAM_ALERTS=true
   ```

## ⚙️ Configuración

Ver `.env.example` para todas las opciones disponibles.

Claves principales:
- `TRADING_MODE`: `paper` (simulación) | `backtest` | `live`
- `INITIAL_CAPITAL`: Capital inicial en pesos
- `ML_MIN_CONFIDENCE`: Confianza mínima para señales (default: 60%)
- `MAX_OPEN_POSITIONS`: Máximo de posiciones simultáneas (default: 8)

## ⚠️ Disclaimer

Este software es para fines educativos e informativos. **No es asesoramiento financiero.** 
Operar en mercados financieros conlleva riesgo de pérdida de capital. 
Siempre verificar señales con análisis propio antes de operar.

## 🗺️ Roadmap

- [x] Scanner dinámico de oportunidades
- [x] Análisis técnico multi-indicador
- [x] ML con XGBoost
- [x] Dashboard Streamlit completo
- [x] Paper trading con BD
- [x] Telegram alertas
- [x] Backtesting profesional
- [ ] Integración con APIs de brokers argentinos (PPI, IOL, Balanz)
- [ ] Análisis de sentimiento de noticias
- [ ] Estrategias de opciones
- [ ] Exportación de reportes PDF
- [ ] Docker para deploy
