"""
dashboard/app.py — Alpha Arena Pro v5
Estilo: azul marino oscuro + cian + naranja, inspirado en RaceWeekend Analysis.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
import asyncio
from typing import List, Dict

from config.settings import settings

st.set_page_config(page_title="Alpha Arena Pro", page_icon="◈", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""
<!-- v5 -->
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --bg0:    #0d1117;
  --bg1:    #131929;
  --bg2:    #1a2235;
  --bg3:    #202d42;
  --b0:     rgba(255,255,255,0.06);
  --b1:     rgba(255,255,255,0.12);
  --b2:     rgba(255,255,255,0.20);
  --cyan:   #38bdf8;
  --cyan2:  #0ea5e9;
  --cyan-d: rgba(56,189,248,0.12);
  --cyan-b: rgba(56,189,248,0.28);
  --orange: #fb923c;
  --orange-d: rgba(251,146,60,0.12);
  --green:  #4ade80;
  --green-d: rgba(74,222,128,0.10);
  --red:    #f87171;
  --red-d:  rgba(248,113,113,0.10);
  --amber:  #fbbf24;
  --t1: #f0f6ff;
  --t2: #94a3b8;
  --t3: #4a5568;
  --fh: 'Inter', sans-serif;
  --fm: 'JetBrains Mono', monospace;
}

html, body, .main, [data-testid="stAppViewContainer"] {
  background: var(--bg0) !important;
  font-family: var(--fh);
  color: var(--t1);
}
#MainMenu, footer, header, [data-testid="stToolbar"] { display:none !important; }
.block-container { padding:1.5rem 2rem 3rem !important; max-width:100% !important; }

/* Sidebar - always visible, no collapse */
[data-testid="stSidebar"] {
  background: var(--bg1) !important;
  border-right: 1px solid var(--b0) !important;
  min-width: 240px !important;
  transform: none !important;
  margin-left: 0 !important;
  visibility: visible !important;
}
/* Collapse/expand button - always visible and styled */
[data-testid="stSidebarCollapsedControl"] {
  display: flex !important;
  background: var(--bg2) !important;
  border: 1px solid var(--b1) !important;
  border-radius: 0 8px 8px 0 !important;
}
[data-testid="stSidebarCollapsedControl"] button {
  color: var(--cyan) !important;
  background: transparent !important;
  border: none !important;
}
[data-testid="collapsedControl"] {
  display: flex !important;
  background: var(--bg2) !important;
  border: 1px solid var(--b1) !important;
  border-radius: 0 8px 8px 0 !important;
  color: var(--cyan) !important;
}
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
button[kind="header"] { display: none !important; }
.st-emotion-cache-dvne4q { display: none !important; }
section[data-testid="stSidebar"] { transform: none !important; width: 240px !important; }
section[data-testid="stSidebar"][aria-expanded="false"] { transform: none !important; margin-left: 0 !important; }
.st-emotion-cache-1rtdyuf { display: none !important; }
.st-emotion-cache-pkbazv { display: none !important; }

/* Botones - estilo RaceWeekend: borde redondeado, outline */
.stButton > button {
  background: transparent !important;
  color: var(--cyan) !important;
  border: 1.5px solid var(--cyan-b) !important;
  border-radius: 20px !important;
  font-family: var(--fm) !important;
  font-size: 0.72rem !important;
  font-weight: 500 !important;
  letter-spacing: 0.05em !important;
  padding: 0.4rem 1.1rem !important;
  transition: all 0.18s !important;
}
.stButton > button:hover {
  background: var(--cyan-d) !important;
  border-color: var(--cyan) !important;
  box-shadow: 0 0 12px rgba(56,189,248,0.20) !important;
  transform: translateY(-1px) !important;
}

/* Métricas */
[data-testid="stMetric"] {
  background: var(--bg2) !important;
  border: 1px solid var(--b0) !important;
  border-radius: 10px !important;
  padding: 1rem 1.25rem !important;
}
[data-testid="stMetric"] label {
  font-family: var(--fm) !important;
  font-size: 0.6rem !important;
  letter-spacing: 0.12em !important;
  color: var(--t3) !important;
  text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
  font-family: var(--fm) !important;
  font-size: 1.35rem !important;
  font-weight: 600 !important;
  color: var(--cyan) !important;
}
[data-testid="stMetricDelta"] { font-family: var(--fm) !important; font-size: 0.7rem !important; }

/* Tabs */
[data-testid="stTabs"] [role="tablist"] {
  background: var(--bg2) !important; border: 1px solid var(--b0) !important;
  border-radius: 8px !important; padding: 3px !important; gap: 2px !important;
}
[data-testid="stTabs"] [role="tab"] {
  font-family: var(--fm) !important; font-size: 0.7rem !important;
  color: var(--t2) !important; border-radius: 6px !important; padding: 5px 16px !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
  background: var(--bg3) !important; color: var(--cyan) !important;
}

/* Selectbox */
div[data-testid="stSelectbox"] label {
  font-family: var(--fm) !important; font-size: 0.68rem !important;
  color: var(--t2) !important; letter-spacing: 0.05em !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
  border: 1px solid var(--b0) !important; border-radius: 10px !important; overflow: hidden !important;
}

hr { border-color: var(--b0) !important; margin: 1.25rem 0 !important; }
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg0); }
::-webkit-scrollbar-thumb { background: var(--b1); border-radius: 2px; }

/* Page header */
.ph { display:flex; align-items:flex-end; justify-content:space-between;
      margin-bottom:1.5rem; padding-bottom:1rem; border-bottom:1px solid var(--b0); }
.ph-title { font-family:var(--fh); font-size:1.4rem; font-weight:700;
            color:var(--t1); letter-spacing:-0.01em; }
.ph-sub { font-family:var(--fm); font-size:0.58rem; color:var(--t3);
          letter-spacing:0.12em; margin-top:3px; text-transform:uppercase; }
.ph-ts { font-family:var(--fm); font-size:0.62rem; color:var(--t3); }

/* Cards */
.card { background:var(--bg2); border:1px solid var(--b0); border-radius:12px;
        padding:1.25rem 1.5rem; margin-bottom:0.75rem; }

/* Badges */
.badge { font-family:var(--fm); font-size:0.58rem; padding:2px 9px;
         border-radius:100px; letter-spacing:0.1em; text-transform:uppercase; }
.bc { background:var(--cyan-d); color:var(--cyan); border:1px solid var(--cyan-b); }
.bo { background:var(--orange-d); color:var(--orange); border:1px solid rgba(251,146,60,0.3); }
.bg { background:var(--green-d); color:var(--green); border:1px solid rgba(74,222,128,0.25); }
.br { background:var(--red-d); color:var(--red); border:1px solid rgba(248,113,113,0.25); }
.ba { background:rgba(251,191,36,0.08); color:var(--amber); border:1px solid rgba(251,191,36,0.2); }

/* Table */
.t { width:100%; border-collapse:collapse; }
.t th { font-family:var(--fm); font-size:0.58rem; letter-spacing:0.1em; color:var(--t3);
        text-transform:uppercase; padding:0.22rem 0.9rem; border-bottom:1px solid var(--b0); text-align:right; }
.t th:first-child { text-align:left; }
.t td { font-family:var(--fm); font-size:0.78rem; color:var(--t1); padding:0.22rem 0.9rem;
        border-bottom:1px solid var(--b0); text-align:right; }
.t td:first-child { text-align:left; }
.t tr:last-child td { border-bottom:none; }
.t tr:hover td { background:var(--bg3); }
.up { color:var(--green) !important; }
.dn { color:var(--red) !important; }
.nt { color:var(--t3) !important; }

/* Signal cards */
.sg { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-bottom:1.25rem; }
.sc { background:var(--bg2); border:1px solid var(--b0); border-radius:12px;
      padding:1.1rem 1.25rem; position:relative; overflow:hidden; transition:all 0.18s; }
.sc::after { content:''; position:absolute; top:0; left:0; right:0; height:2px; }
.sc.buy::after  { background:linear-gradient(90deg, var(--green), transparent); }
.sc.sell::after { background:linear-gradient(90deg, var(--red), transparent); }
.sc.hold::after { background:linear-gradient(90deg, var(--amber), transparent); }
.sc:hover { border-color:var(--b1); }
.sc-h { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.75rem; }
.sc-sym { font-family:var(--fh); font-size:1rem; font-weight:700; color:var(--t1); }
.sc-mkt { font-size:0.63rem; color:var(--t3); margin-top:2px; }
.sc-px { font-family:var(--fm); font-size:1.1rem; color:var(--cyan); margin-bottom:0.6rem; }
.sc-g { display:grid; grid-template-columns:1fr 1fr; gap:5px; }
.sc-m { background:var(--bg3); border-radius:6px; padding:5px 8px; }
.sc-ml { font-family:var(--fm); font-size:0.56rem; color:var(--t3); letter-spacing:0.08em; text-transform:uppercase; }
.sc-mv { font-family:var(--fm); font-size:0.77rem; color:var(--t1); margin-top:1px; }
.sc-bar { margin-top:0.6rem; }
.sc-bl { display:flex; justify-content:space-between; font-family:var(--fm); font-size:0.58rem; color:var(--t3); margin-bottom:3px; }
.sc-bt { height:2px; background:var(--bg3); border-radius:2px; overflow:hidden; }
.sc-bf { height:100%; border-radius:2px; }

/* Section */
.sh { display:flex; align-items:center; justify-content:space-between; margin:1.25rem 0 0.75rem; }
.sh-t { font-family:var(--fh); font-size:0.9rem; font-weight:600; color:var(--t1); }
.sh-c { font-family:var(--fm); font-size:0.62rem; color:var(--t2);
        background:var(--bg2); border:1px solid var(--b0); padding:2px 10px; border-radius:100px; }

/* ML banner */
.mlb { border-radius:12px; padding:1.5rem 2rem; margin-bottom:1.25rem;
       display:flex; align-items:center; gap:2rem; }
.ml-s { font-family:var(--fh); font-size:2.5rem; font-weight:800; line-height:1; }
.ml-g { flex:1; display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
.ml-i { background:var(--bg3); border-radius:8px; padding:0.75rem; }
.ml-il { font-family:var(--fm); font-size:0.56rem; color:var(--t3); text-transform:uppercase; letter-spacing:0.08em; }
.ml-iv { font-family:var(--fh); font-size:1.2rem; font-weight:700; margin-top:2px; }

.warn { background:rgba(251,191,36,0.06); border:1px solid rgba(251,191,36,0.18);
        border-radius:8px; padding:0.6rem 1rem; font-family:var(--fm);
        font-size:0.68rem; color:var(--amber); margin-bottom:1rem; }
</style>
""", unsafe_allow_html=True)

PT = dict(
    template="plotly_dark", paper_bgcolor="#0d1117", plot_bgcolor="#131929",
    font=dict(family="JetBrains Mono, monospace", color="#94a3b8", size=11),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.06)", zeroline=False),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.06)", zeroline=False),
    margin=dict(l=8, r=8, t=32, b=8),
)

@st.cache_data(ttl=30)
def load_quotes(tickers):
    from core.data_fetcher import data_fetcher
    return {t: data_fetcher.get_quote(t) for t in tickers}

@st.cache_data(ttl=300)
def load_history(ticker, days=180):
    from core.data_fetcher import data_fetcher
    return data_fetcher.get_history(ticker, days)

@st.cache_data(ttl=120)
def scan_market():
    from core.data_fetcher import data_fetcher
    return data_fetcher.scan_opportunities(top_n=15)

@st.cache_data(ttl=90)
def get_ta(ticker):
    from core.data_fetcher import data_fetcher
    from strategies.technical import technical_analyzer
    df = data_fetcher.get_history(ticker, 200)
    if df.empty: return {}
    r = technical_analyzer.analyze(df, ticker)
    return {"signal":r.signal,"ta_score":r.ta_score,"confidence":r.confidence,
            "reasons":r.reasons,"indicators":r.indicators}

def get_ml(ticker):
    from core.data_fetcher import data_fetcher
    from strategies.ml_predictor import MLPredictor
    import numpy as np

    cache_key = f"ml_result_{ticker}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]

    df = data_fetcher.get_history(ticker, 500)
    if df.empty or len(df) < 100:
        return {"error": "datos insuficientes", "n_rows": len(df) if not df.empty else 0}

    # Crear instancia fresca — en cloud no hay persistencia en disco
    predictor = MLPredictor()

    try:
        # Entrenar siempre en cloud (no hay modelos guardados)
        meta = predictor.train(df, ticker)
        if not meta:
            return {"error": f"entrenamiento fallido — filas: {len(df)}"}

        pred = predictor.predict(df, ticker)

        # Verificar que el resultado es válido
        if pred.probability == 0.0 and pred.signal == "HOLD" and pred.model_accuracy == 0.0:
            return {"error": "predicción inválida — modelo no convergió"}

        result = {
            "signal": pred.signal,
            "proba": pred.probability,
            "accuracy": pred.model_accuracy,
            "features": pred.features_used,
            "trained_at": pred.trained_at,
            "n_samples": meta.get("n_samples", 0),
            "class_dist": meta.get("class_distribution", {}),
        }
        st.session_state[cache_key] = result
        return result

    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=300)
def get_backtest(ticker, strategy, days):
    from core.data_fetcher import data_fetcher
    from strategies.backtester import backtester
    df = data_fetcher.get_history(ticker, days)
    if df.empty or len(df) < 60: return {}
    try:
        r = backtester.run(df, ticker=ticker, strategy=strategy)
        return {"summary":r.summary_dict(),"equity":r.equity_curve,"drawdown":r.drawdown_curve,
                "trades":r.trades,"total_return":r.total_return_pct,"sharpe":r.sharpe_ratio,
                "max_dd":r.max_drawdown_pct,"win_rate":r.win_rate}
    except Exception as e:
        return {"error":str(e)}


def ticker_selector(key: str = "ticker") -> str:
    """Selector de ticker: dropdown predefinido + campo libre."""
    all_t = settings.merval_universe + settings.cedear_universe
    
    col1, col2 = st.columns([3, 2])
    with col1:
        selected = st.selectbox("Activo del universo", all_t, key=f"{key}_select")
    with col2:
        custom = st.text_input(
            "O escribí cualquier ticker",
            placeholder="Ej: VIST, LOMA, TSLA, MELI...",
            key=f"{key}_custom"
        ).strip().upper()
    
    if custom:
        # Validate ticker exists in yfinance
        try:
            import yfinance as yf
            test = yf.Ticker(custom)
            hist = test.history(period="5d")
            if not hist.empty:
                return custom
            else:
                st.warning(f"⚠ No se encontraron datos para '{custom}'. Verificá el ticker.")
                return selected
        except Exception:
            st.warning(f"⚠ Ticker '{custom}' no válido.")
            return selected
    return selected


def ph(title, sub):
    st.markdown(f"""
    <div class="ph">
      <div><div class="ph-title">{title}</div><div class="ph-sub">{sub}</div></div>
      <div class="ph-ts">{datetime.now().strftime('%d %b %Y · %H:%M:%S')}</div>
    </div>""", unsafe_allow_html=True)


def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="padding:1.75rem 1.25rem 1rem;border-bottom:1px solid var(--b0);margin-bottom:0.5rem">
          <div style="font-family:var(--fm);font-size:0.82rem;font-weight:600;color:var(--cyan);letter-spacing:0.15em">◈ ALPHA ARENA PRO</div>
          <div style="font-family:var(--fm);font-size:0.58rem;color:var(--t3);letter-spacing:0.08em;margin-top:4px">MERVAL · CEDEARS · v2.0</div>
        </div>""", unsafe_allow_html=True)

        if "page" not in st.session_state:
            st.session_state["page"] = "Dashboard"

        for icon, name in [("▦","Dashboard"),("◈","Scanner"),("◎","Análisis"),
                            ("⬡","ML Predictor"),("◷","Backtest"),("◻","Portfolio")]:
            if st.button(f"{icon}  {name}", key=f"nav_{name}", use_container_width=True):
                st.session_state["page"] = name
                st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="padding:0 0.75rem;font-family:var(--fm);font-size:0.65rem;color:var(--t2);line-height:2.1">
          <span style="background:var(--orange-d);color:var(--orange);border:1px solid rgba(251,146,60,0.25);
                       padding:2px 9px;border-radius:100px;font-size:0.6rem">● {settings.trading_mode.upper()}</span><br>
          Capital <span style="color:var(--t1)">${settings.initial_capital:,.0f}</span><br>
          Universo <span style="color:var(--t1)">{len(settings.all_tickers)} activos</span><br>
          ML mín <span style="color:var(--t1)">{settings.ml_min_confidence:.0%}</span>
        </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        if st.button("↺  Refrescar", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.markdown(f"""
        <div style="padding:0.75rem 0.75rem 0;font-family:var(--fm);font-size:0.58rem;
                    color:var(--t3);border-top:1px solid var(--b0);margin-top:0.75rem">
          {datetime.now().strftime('%d/%m/%Y  %H:%M:%S')}
        </div>""", unsafe_allow_html=True)

    return st.session_state.get("page","Dashboard")


def page_dashboard():
    ph("Mercado", "Cotizaciones en tiempo real · Yahoo Finance")
    tab1, tab2 = st.tabs(["▦  MERVAL", "◈  CEDEARs"])
    with tab1: _tbl(settings.merval_universe[:12], "MERVAL", "bc")
    with tab2: _tbl(settings.cedear_universe, "CEDEAR", "bo")

def _tbl(tickers, label, bcls):
    with st.spinner(""):
        data = load_quotes(tuple(tickers))
    rows = [(t,q) for t,q in data.items() if q.get("ok")]
    if not rows:
        st.warning("Sin datos."); return

    # Build entire table in ONE markdown call to avoid HTML fragmentation
    tbody = ""
    for ticker, q in rows:
        chg = q["change"]
        cls = "up" if chg>0 else ("dn" if chg<0 else "nt")
        sign = "+" if chg>0 else ""
        v = q["volume"]
        vs = f"{v/1e6:.1f}M" if v>1e6 else (f"{v/1e3:.0f}K" if v>1000 else str(v))
        tbody += f"""<tr>
          <td style="text-align:left">
            <span style="color:var(--t1);font-weight:600">{ticker.replace(".BA","")}</span>
            <span style="color:var(--t3);font-size:0.65rem;margin-left:6px">{ticker}</span>
          </td>
          <td style="color:var(--cyan);text-align:right">${q["price"]:,.2f}</td>
          <td style="text-align:right"><span class="{cls}">{sign}{chg:.2f}%</span></td>
          <td style="text-align:right">${q["high"]:,.2f}</td>
          <td style="text-align:right">${q["low"]:,.2f}</td>
          <td style="color:var(--t2);text-align:right">{vs}</td>
        </tr>"""

    st.markdown(f"""
    <div class="card">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem">
        <div style="display:flex;align-items:center;gap:8px">
          <span class="badge {bcls}">{label}</span>
          <span style="font-family:var(--fm);font-size:0.68rem;color:var(--t2)">{len(rows)} activos</span>
        </div>
        <span style="font-family:var(--fm);font-size:0.6rem;color:var(--t3)">{datetime.now().strftime("%H:%M:%S")}</span>
      </div>
      <table class="t">
        <thead><tr>
          <th style="text-align:left;width:20%">Ticker</th>
          <th style="text-align:right;width:15%">Precio</th>
          <th style="text-align:right;width:12%">Cambio</th>
          <th style="text-align:right;width:15%">Máximo</th>
          <th style="text-align:right;width:15%">Mínimo</th>
          <th style="text-align:right;width:10%">Volumen</th>
        </tr></thead>
        <tbody>{tbody}</tbody>
      </table>
    </div>
    """, unsafe_allow_html=True)


def page_scanner():
    ph("Scanner", "Ranking dinámico · Momentum + Volumen + RSI + Tendencia")
    c1,c2 = st.columns([5,1])
    with c2:
        if st.button("↺ Escanear", use_container_width=True): st.cache_data.clear()

    with st.spinner("Escaneando mercado..."): df = scan_market()
    if df.empty: st.warning("Sin resultados."); return

    def classify(rsi):
        if 25<rsi<45: return "BUY","buy","bg","var(--green)"
        if rsi>65:    return "SELL","sell","br","var(--red)"
        return "HOLD","hold","ba","var(--amber)"

    st.markdown('<div class="sh"><span class="sh-t">Top Oportunidades</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="sg">', unsafe_allow_html=True)

    for _,row in df.head(3).iterrows():
        lbl,cls,bcls,color = classify(row['rsi'])
        sp = int(row['score']*100)
        cc = "var(--green)" if row['change']>=0 else "var(--red)"
        sg = "+" if row['change']>=0 else ""
        st.markdown(f"""
        <div class="sc {cls}">
          <div class="sc-h">
            <div>
              <div class="sc-sym">{row['ticker'].replace('.BA','')}</div>
              <div class="sc-mkt">{row['ticker']} · {row['market']}</div>
            </div>
            <span class="badge {bcls}">{lbl}</span>
          </div>
          <div class="sc-px">${row['price']:,.2f} <span style="font-size:0.7rem;color:{cc};margin-left:6px">{sg}{row['change']:.2f}%</span></div>
          <div class="sc-g">
            <div class="sc-m"><div class="sc-ml">RSI</div><div class="sc-mv">{row['rsi']:.1f}</div></div>
            <div class="sc-m"><div class="sc-ml">Ret 20d</div><div class="sc-mv" style="color:{cc}">{"+" if row['ret_20d']>=0 else ""}{row['ret_20d']:.1f}%</div></div>
            <div class="sc-m"><div class="sc-ml">Vol ×</div><div class="sc-mv">{row['rel_volume']:.1f}x</div></div>
            <div class="sc-m"><div class="sc-ml">vs SMA50</div><div class="sc-mv">{"+" if row['vs_sma50_pct']>=0 else ""}{row['vs_sma50_pct']:.1f}%</div></div>
          </div>
          <div class="sc-bar">
            <div class="sc-bl"><span>Score</span><span style="color:{color};font-weight:500">{sp}%</span></div>
            <div class="sc-bt"><div class="sc-bf" style="width:{sp}%;background:{color}"></div></div>
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(f'<div class="sh" style="margin-top:1.5rem"><span class="sh-t">Ranking Completo</span><span class="sh-c">{len(df)} activos</span></div>', unsafe_allow_html=True)

    disp = df[["ticker","market","price","change","score","rsi","ret_5d","ret_20d","rel_volume","vs_sma50_pct"]].copy()
    disp.columns = ["Ticker","Mercado","Precio","Cambio%","Score","RSI","Ret5d%","Ret20d%","Vol×","vsSMA50%"]
    styled = (disp.style
        .map(lambda v: ("background:#0a2218;color:#4ade80" if v>=0.6 else "background:#1a1500;color:#fbbf24" if v>=0.4 else "background:#2d0a0a;color:#f87171") if isinstance(v,float) and 0<=v<=1 else "", subset=["Score"])
        .map(lambda v: f"color:{'#4ade80' if v>=0 else '#f87171'}" if isinstance(v,(int,float)) else "", subset=["Cambio%","Ret5d%","Ret20d%","vsSMA50%"])
        .format({"Precio":"${:,.2f}","Cambio%":"{:+.2f}%","Score":"{:.0%}","RSI":"{:.0f}",
                 "Ret5d%":"{:+.1f}%","Ret20d%":"{:+.1f}%","Vol×":"{:.1f}x","vsSMA50%":"{:+.1f}%"}, na_rep="—"))
    st.dataframe(styled, use_container_width=True, hide_index=True)

    df["Señal"] = df["rsi"].apply(lambda r: "BUY" if 25<r<45 else ("SELL" if r>65 else "HOLD"))
    fig = px.scatter(df, x="ret_20d", y="score", size="rel_volume", color="Señal",
        hover_data=["ticker","rsi","price"],
        color_discrete_map={"BUY":"#4ade80","SELL":"#f87171","HOLD":"#fbbf24"},
        labels={"ret_20d":"Retorno 20d (%)","score":"Score"})
    fig.add_vline(x=0, line_dash="dash", line_color="rgba(255,255,255,0.08)")
    fig.add_hline(y=0.5, line_dash="dash", line_color="rgba(255,255,255,0.08)")
    fig.update_layout(**PT, height=360)
    fig.update_traces(marker=dict(line=dict(width=0)))
    st.plotly_chart(fig, use_container_width=True)


def page_analysis():
    ph("Análisis Técnico", "RSI · MACD · Bollinger · EMA20/50/200 · Stochastic · ADX")
    c1, c2 = st.columns([2, 1])
    with c1:
        ticker = ticker_selector("analysis")
    with c2:
        period = st.selectbox("Período", ["3M","6M","1A","2A"])
    days = {"3M":90,"6M":180,"1A":365,"2A":730}[period]

    with st.spinner(""):
        df = load_history(ticker, days)
        ta = get_ta(ticker)
    if df.empty: st.warning(f"Sin datos para {ticker}"); return

    if ta:
        sig = ta.get("signal","HOLD"); sc = ta.get("ta_score",0)
        cf = ta.get("confidence",0); ind = ta.get("indicators",{})
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("Señal TA", sig, delta=f"Score {sc:+.2f}")
        c2.metric("Confianza", f"{cf:.0%}")
        c3.metric("RSI", f"{ind.get('rsi',50):.1f}")
        c4.metric("MACD Hist", f"{ind.get('macd_hist',0):.4f}")
        c5.metric("Precio", f"${df['Close'].iloc[-1]:,.2f}")
        if ta.get("reasons"):
            st.markdown(f"""<div class="card" style="padding:0.6rem 1rem;margin:0.75rem 0">
              <span style="font-family:var(--fm);font-size:0.68rem;color:var(--t2)">{" · ".join(ta['reasons'])}</span>
            </div>""", unsafe_allow_html=True)

    from strategies.technical import TechnicalAnalyzer
    df_i = TechnicalAnalyzer.get_indicators_df(df)
    fig = make_subplots(rows=4,cols=1,shared_xaxes=True,vertical_spacing=0.02,
        row_heights=[0.52,0.18,0.16,0.14],subplot_titles=[ticker,"MACD","RSI","Volumen"])

    fig.add_trace(go.Candlestick(x=df.index,open=df["Open"],high=df["High"],low=df["Low"],close=df["Close"],
        name="",showlegend=False,
        increasing=dict(line=dict(color="#4ade80"),fillcolor="rgba(74,222,128,0.7)"),
        decreasing=dict(line=dict(color="#f87171"),fillcolor="rgba(248,113,113,0.7)")),row=1,col=1)

    if "bb_upper" in df_i.columns:
        for cn,a in [("bb_upper",0.3),("bb_mid",0.5),("bb_lower",0.3)]:
            fig.add_trace(go.Scatter(x=df_i.index,y=df_i[cn],
                line=dict(color=f"rgba(56,189,248,{a})",width=1),showlegend=False),row=1,col=1)
        fig.add_trace(go.Scatter(x=list(df_i.index)+list(df_i.index[::-1]),
            y=list(df_i["bb_upper"])+list(df_i["bb_lower"][::-1]),
            fill="toself",fillcolor="rgba(56,189,248,0.04)",
            line=dict(color="rgba(0,0,0,0)"),showlegend=False),row=1,col=1)

    for ema,color in [("ema20","#fbbf24"),("ema50","#a78bfa"),("ema200","rgba(248,113,113,0.65)")]:
        if ema in df_i.columns:
            fig.add_trace(go.Scatter(x=df_i.index,y=df_i[ema],
                line=dict(color=color,width=1.2),name=ema.upper()),row=1,col=1)

    if "macd" in df_i.columns:
        fig.add_trace(go.Scatter(x=df_i.index,y=df_i["macd"],line=dict(color="#38bdf8",width=1.5),name="MACD"),row=2,col=1)
        fig.add_trace(go.Scatter(x=df_i.index,y=df_i["macd_signal"],line=dict(color="#fbbf24",width=1.5),name="Signal"),row=2,col=1)
        ch = ["#4ade80" if v>=0 else "#f87171" for v in df_i["macd_hist"].fillna(0)]
        fig.add_trace(go.Bar(x=df_i.index,y=df_i["macd_hist"],marker_color=ch,showlegend=False),row=2,col=1)

    if "rsi" in df_i.columns:
        fig.add_trace(go.Scatter(x=df_i.index,y=df_i["rsi"],
            line=dict(color="#a78bfa",width=1.8),showlegend=False),row=3,col=1)
        fig.add_hline(y=70,line_dash="dot",line_color="rgba(248,113,113,0.4)",row=3,col=1)
        fig.add_hline(y=30,line_dash="dot",line_color="rgba(74,222,128,0.4)",row=3,col=1)
        fig.add_hrect(y0=30,y1=70,fillcolor="rgba(255,255,255,0.015)",line_width=0,row=3,col=1)

    vc = ["#4ade80" if c>=o else "#f87171" for c,o in zip(df["Close"],df["Open"])]
    fig.add_trace(go.Bar(x=df.index,y=df["Volume"],marker_color=vc,showlegend=False),row=4,col=1)
    fig.update_layout(**PT,height=820,xaxis_rangeslider_visible=False,
        legend=dict(orientation="h",y=1.02,font=dict(size=10)))
    st.plotly_chart(fig, use_container_width=True)


def page_ml():
    ph("ML Predictor", "XGBoost · 30+ Features · Time-Series CV · Horizonte 5 días")
    c1, c2 = st.columns([3, 1])
    with c1:
        ticker = ticker_selector("ml")
    with c2:
        st.write(""); st.write("")
        btn = st.button("⬡ Predecir", use_container_width=True)

    if not btn and "ml_ticker" not in st.session_state:
        st.markdown("""<div class="card" style="padding:2.5rem;text-align:center">
          <div style="font-family:var(--fh);font-size:1rem;color:var(--t2);margin-bottom:0.4rem">Seleccioná un activo y presioná Predecir</div>
          <div style="font-family:var(--fm);font-size:0.68rem;color:var(--t3)">Primera vez tarda ~1 min — entrena con datos históricos reales</div>
        </div>""", unsafe_allow_html=True)
        return

    if btn:
        # Clear previous result when new ticker selected
        old_ticker = st.session_state.get("ml_ticker", "")
        if old_ticker != ticker:
            cache_key = f"ml_result_{old_ticker}"
            if cache_key in st.session_state:
                del st.session_state[cache_key]
        st.session_state["ml_ticker"] = ticker

    active = st.session_state.get("ml_ticker", ticker)

    with st.spinner(f"Entrenando modelo para {active}... (puede tardar 1-2 min)"):
        res = get_ml(active)

    if not res:
        st.error("Sin respuesta del modelo.")
        return

    if "error" in res:
        st.error(f"No se pudo generar predicción: {res['error']}")
        return

    sig   = res.get("signal", "HOLD")
    proba = res.get("proba", 0)
    acc   = res.get("accuracy", 0)
    clrs  = {
        "BUY":  ("var(--green)", "rgba(74,222,128,0.06)",  "rgba(74,222,128,0.2)"),
        "SELL": ("var(--red)",   "rgba(248,113,113,0.06)", "rgba(248,113,113,0.2)"),
        "HOLD": ("var(--amber)", "rgba(251,191,36,0.06)",  "rgba(251,191,36,0.2)"),
    }
    color, bg, border = clrs.get(sig, clrs["HOLD"])

    # Distribución de clases para transparencia
    class_dist = res.get("class_dist", {})
    n_samples  = res.get("n_samples", 0)

    st.markdown(f"""
    <div class="mlb" style="background:{bg};border:1px solid {border}">
      <div>
        <div style="font-family:var(--fm);font-size:0.56rem;color:var(--t3);letter-spacing:0.12em;text-transform:uppercase;margin-bottom:5px">Predicción ML · {active}</div>
        <div class="ml-s" style="color:{color}">{sig}</div>
        <div style="font-family:var(--fm);font-size:0.6rem;color:var(--t3);margin-top:4px">{n_samples} muestras de entrenamiento</div>
      </div>
      <div class="ml-g">
        <div class="ml-i"><div class="ml-il">Confianza</div><div class="ml-iv" style="color:{color}">{proba:.0%}</div></div>
        <div class="ml-i"><div class="ml-il">Accuracy CV</div><div class="ml-iv" style="color:var(--t1)">{acc:.1%}</div></div>
        <div class="ml-i"><div class="ml-il">Features</div><div class="ml-iv" style="color:var(--t1)">{res.get("features",0)}</div></div>
      </div>
    </div>
    <div class="warn">⚠ Predicciones probabilísticas — siempre combinar con análisis técnico y gestión de riesgo</div>
    """, unsafe_allow_html=True)


def page_backtest():
    ph("Backtest", "Sharpe · Sortino · Max Drawdown · Win Rate · Profit Factor")
    c1,c2,c3,c4 = st.columns(4)
    with c1: ticker = ticker_selector("backtest")
    with c2:
        strat = st.selectbox("Estrategia",["technical","momentum","mean_reversion"],
            format_func=lambda x:{"technical":"Análisis Técnico","momentum":"Momentum","mean_reversion":"Mean Reversion"}[x])
    with c3:
        period = st.selectbox("Período",["6M","1A","2A"])
        days = {"6M":180,"1A":365,"2A":730}[period]
    with c4:
        st.write(""); st.write("")
        run = st.button("▶ Ejecutar", use_container_width=True)

    if not run and "bt_result" not in st.session_state:
        st.info("Configurá los parámetros y presioná Ejecutar."); return

    if run:
        with st.spinner("Ejecutando..."): st.session_state["bt_result"] = get_backtest(ticker,strat,days)

    res = st.session_state.get("bt_result",{})
    if not res or "error" in res: st.error(res.get("error","Error.")); return

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("Retorno Total", f"{res['total_return']:+.1f}%")
    c2.metric("Sharpe", f"{res['sharpe']:.2f}")
    c3.metric("Max DD", f"-{res['max_dd']:.1f}%")
    c4.metric("Win Rate", f"{res['win_rate']:.0%}")
    c5.metric("Trades", res['summary'].get('Total Trades','—'))
    c6.metric("Profit Factor", res['summary'].get('Profit Factor','—'))

    eq = res.get("equity"); dd = res.get("drawdown")
    if eq is not None and not eq.empty:
        fig = make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=0.04,row_heights=[0.70,0.30])
        fig.add_trace(go.Scatter(x=eq.index,y=eq.values,fill="tozeroy",
            line=dict(color="#38bdf8",width=2),fillcolor="rgba(56,189,248,0.06)",name="Capital"),row=1,col=1)
        fig.add_hline(y=settings.initial_capital,line_dash="dot",line_color="rgba(255,255,255,0.12)",row=1,col=1)
        if dd is not None and not dd.empty:
            fig.add_trace(go.Scatter(x=dd.index,y=dd.values,fill="tozeroy",
                line=dict(color="#f87171",width=1.5),fillcolor="rgba(248,113,113,0.10)",name="Drawdown"),row=2,col=1)
        fig.update_layout(**PT,height=460)
        st.plotly_chart(fig, use_container_width=True)

    trades = res.get("trades",[])
    if trades:
        st.markdown(f'<div class="sh"><span class="sh-t">Historial — {min(50,len(trades))} trades</span></div>', unsafe_allow_html=True)
        rows = [{"Entrada":t.entry_date[:10],"Salida":t.exit_date[:10],"Lado":t.side,
                 "$ Entrada":round(t.entry_price,2),"$ Salida":round(t.exit_price,2),
                 "P&L $":round(t.pnl,2),"P&L %":round(t.pnl_pct,2)} for t in trades[-50:]]
        df_t = pd.DataFrame(rows)
        styled = df_t.style.map(lambda v: f"color:{'#4ade80' if v>=0 else '#f87171'}" if isinstance(v,(int,float)) else "", subset=["P&L $","P&L %"])
        st.dataframe(styled, use_container_width=True, hide_index=True)


def page_portfolio():
    ph("Portfolio", "Paper trading · Posiciones abiertas · Historial")
    try:
        from core.database import db
        async def _get():
            await db.initialize()
            return await db.get_open_trades(), await db.get_recent_trades(50), await db.get_trade_stats()
        with st.spinner(""): open_t,recent_t,stats = asyncio.run(_get())

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("P&L Total",   f"${stats['total_pnl']:,.2f}")
        c2.metric("Win Rate",    f"{stats['win_rate']:.0%}")
        c3.metric("Trades",      str(stats['closed_trades']))
        c4.metric("Mejor Trade", f"${stats['best_trade']:,.2f}")

        st.markdown('<hr>', unsafe_allow_html=True)
        st.markdown('<div class="sh"><span class="sh-t">Posiciones Abiertas</span></div>', unsafe_allow_html=True)

        if open_t:
            rows = [{"Ticker":t.ticker,"Lado":t.side,"Entrada":round(t.entry_price,2),
                     "Qty":t.quantity,"Stop":round(t.stop_loss or 0,2),
                     "Target":round(t.take_profit or 0,2),"Score":round(t.signal_score or 0,2),
                     "Fecha":str(t.entry_time)[:16]} for t in open_t]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.markdown("""<div class="card" style="text-align:center;padding:2rem">
              <span style="font-family:var(--fm);font-size:0.72rem;color:var(--t3)">
                Sin posiciones abiertas · Iniciá el bot con <code>python main.py</code>
              </span></div>""", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error: {e}")


def main():
    page = render_sidebar()
    {"Dashboard":page_dashboard,"Scanner":page_scanner,"Análisis":page_analysis,
     "ML Predictor":page_ml,"Backtest":page_backtest,"Portfolio":page_portfolio}.get(page,page_dashboard)()

if __name__ == "__main__":
    main()
