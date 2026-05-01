"""
dashboard/app.py
Alpha Arena Pro — Dashboard v4
Diseño limpio, moderno y funcional.
"""
import sys
import os
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

st.set_page_config(
    page_title="Alpha Arena Pro",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<!-- v4 -->
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');

:root {
  --bg:          #0a0c14;
  --bg-card:     #111520;
  --bg-hover:    #181d2e;
  --border:      rgba(255,255,255,0.08);
  --border-hi:   rgba(255,255,255,0.16);
  --teal:        #2dd4bf;
  --teal-dim:    rgba(45,212,191,0.12);
  --teal-border: rgba(45,212,191,0.30);
  --violet:      #818cf8;
  --amber:       #fbbf24;
  --red:         #f87171;
  --red-dim:     rgba(248,113,113,0.10);
  --green:       #34d399;
  --text-1:      #f1f5f9;
  --text-2:      #94a3b8;
  --text-3:      #475569;
  --font-h:      'Syne', sans-serif;
  --font-m:      'DM Mono', monospace;
  --font-b:      'DM Sans', sans-serif;
}

html, body, .main, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  font-family: var(--font-b);
  color: var(--text-1);
}

#MainMenu, footer, header, [data-testid="stToolbar"] { display:none !important; }
.block-container { padding: 1.5rem 2rem 3rem !important; max-width:100% !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: #0d1018 !important;
  border-right: 1px solid var(--border) !important;
}

/* ── Botones ── */
.stButton > button {
  background: transparent !important;
  color: var(--teal) !important;
  border: 1.5px solid var(--teal-border) !important;
  border-radius: 8px !important;
  font-family: var(--font-m) !important;
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  letter-spacing: 0.06em !important;
  padding: 0.45rem 1.2rem !important;
  transition: all 0.18s ease !important;
}
.stButton > button:hover {
  background: var(--teal-dim) !important;
  border-color: var(--teal) !important;
  color: var(--teal) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 12px rgba(45,212,191,0.15) !important;
}
.stButton > button:active {
  transform: translateY(0) !important;
}

/* ── Métricas ── */
[data-testid="stMetric"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  padding: 1rem 1.25rem !important;
}
[data-testid="stMetric"] label {
  font-family: var(--font-m) !important;
  font-size: 0.62rem !important;
  letter-spacing: 0.1em !important;
  color: var(--text-2) !important;
  text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
  font-family: var(--font-h) !important;
  font-size: 1.4rem !important;
  font-weight: 700 !important;
  color: var(--text-1) !important;
}
[data-testid="stMetricDelta"] {
  font-family: var(--font-m) !important;
  font-size: 0.72rem !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tablist"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  padding: 3px !important;
  gap: 2px !important;
}
[data-testid="stTabs"] [role="tab"] {
  font-family: var(--font-m) !important;
  font-size: 0.72rem !important;
  color: var(--text-2) !important;
  border-radius: 6px !important;
  padding: 5px 16px !important;
  border: none !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
  background: var(--bg-hover) !important;
  color: var(--text-1) !important;
}

/* ── Selectbox / inputs ── */
div[data-testid="stSelectbox"] label,
div[data-testid="stRadio"] label {
  font-family: var(--font-m) !important;
  font-size: 0.7rem !important;
  color: var(--text-2) !important;
  letter-spacing: 0.05em !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  overflow: hidden !important;
}

/* ── Divider ── */
hr { border-color: var(--border) !important; margin: 1.25rem 0 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border-hi); border-radius: 2px; }

/* ── Cards custom ── */
.aa-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 0.75rem;
}
.aa-card-title {
  font-family: var(--font-h);
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-1);
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  gap: 8px;
}
.aa-badge {
  font-family: var(--font-m);
  font-size: 0.6rem;
  padding: 2px 8px;
  border-radius: 4px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.badge-teal   { background:var(--teal-dim); color:var(--teal); border:1px solid var(--teal-border); }
.badge-violet { background:rgba(129,140,248,0.1); color:var(--violet); border:1px solid rgba(129,140,248,0.25); }
.badge-amber  { background:rgba(251,191,36,0.1); color:var(--amber); border:1px solid rgba(251,191,36,0.25); }
.badge-red    { background:var(--red-dim); color:var(--red); border:1px solid rgba(248,113,113,0.25); }

/* ── Page header ── */
.aa-page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border);
}
.aa-page-title {
  font-family: var(--font-h);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-1);
  letter-spacing: -0.02em;
}
.aa-page-sub {
  font-family: var(--font-m);
  font-size: 0.62rem;
  color: var(--text-3);
  letter-spacing: 0.1em;
  margin-top: 3px;
  text-transform: uppercase;
}
.aa-timestamp {
  font-family: var(--font-m);
  font-size: 0.65rem;
  color: var(--text-3);
}

/* ── Ticker table ── */
.aa-table { width:100%; border-collapse:collapse; }
.aa-table th {
  font-family: var(--font-m);
  font-size: 0.6rem;
  letter-spacing: 0.1em;
  color: var(--text-3);
  text-transform: uppercase;
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--border);
  text-align: right;
}
.aa-table th:first-child { text-align: left; }
.aa-table td {
  font-family: var(--font-m);
  font-size: 0.8rem;
  color: var(--text-1);
  padding: 0.65rem 0.75rem;
  border-bottom: 1px solid var(--border);
  text-align: right;
}
.aa-table td:first-child { text-align: left; }
.aa-table tr:last-child td { border-bottom: none; }
.aa-table tr:hover td { background: var(--bg-hover); }
.t-up   { color: var(--teal) !important; }
.t-down { color: var(--red) !important; }
.t-flat { color: var(--text-3) !important; }

/* ── Signal cards ── */
.sc-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-bottom:1.25rem; }
.sc {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 1.1rem 1.25rem;
  position: relative;
  overflow: hidden;
  transition: all 0.18s;
}
.sc::after {
  content:'';
  position:absolute;
  top:0; left:0; right:0;
  height: 2px;
}
.sc.buy::after  { background: linear-gradient(90deg, var(--teal), transparent); }
.sc.sell::after { background: linear-gradient(90deg, var(--red), transparent); }
.sc.hold::after { background: linear-gradient(90deg, var(--amber), transparent); }
.sc:hover { border-color: var(--border-hi); }

.sc-head { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.8rem; }
.sc-sym  { font-family:var(--font-h); font-size:1rem; font-weight:700; color:var(--text-1); }
.sc-mkt  { font-size:0.65rem; color:var(--text-3); margin-top:2px; }
.sc-price { font-family:var(--font-m); font-size:1.1rem; color:var(--text-1); margin-bottom:0.65rem; }
.sc-grid2 { display:grid; grid-template-columns:1fr 1fr; gap:6px; }
.sc-m { background:var(--bg-hover); border-radius:6px; padding:5px 8px; }
.sc-ml { font-family:var(--font-m); font-size:0.57rem; color:var(--text-3); letter-spacing:0.08em; text-transform:uppercase; }
.sc-mv { font-family:var(--font-m); font-size:0.78rem; color:var(--text-1); margin-top:1px; }
.sc-bar { margin-top:0.65rem; }
.sc-bar-lbl { display:flex; justify-content:space-between; font-family:var(--font-m); font-size:0.6rem; color:var(--text-3); margin-bottom:3px; }
.sc-bar-track { height:2px; background:var(--bg-hover); border-radius:2px; overflow:hidden; }
.sc-bar-fill { height:100%; border-radius:2px; }

/* ── Section header ── */
.aa-sec { display:flex; align-items:center; justify-content:space-between; margin:1.25rem 0 0.75rem; }
.aa-sec-title { font-family:var(--font-h); font-size:0.95rem; font-weight:600; color:var(--text-1); }
.aa-sec-count {
  font-family:var(--font-m); font-size:0.65rem; color:var(--text-2);
  background:var(--bg-card); border:1px solid var(--border);
  padding:2px 10px; border-radius:100px;
}

/* ── Sidebar pills ── */
.sb-status {
  display:inline-flex; align-items:center; gap:5px;
  font-family:var(--font-m); font-size:0.68rem; font-weight:500;
  padding:3px 10px; border-radius:100px;
  background:rgba(251,191,36,0.08); color:var(--amber);
  border:1px solid rgba(251,191,36,0.2);
}

/* ── ML result banner ── */
.ml-banner {
  border-radius: 12px;
  padding: 1.5rem 2rem;
  margin-bottom: 1.25rem;
  display: flex;
  align-items: center;
  gap: 2rem;
}
.ml-sig {
  font-family: var(--font-h);
  font-size: 2.5rem;
  font-weight: 800;
  line-height: 1;
}
.ml-grid { flex:1; display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }
.ml-stat { background:var(--bg-hover); border-radius:8px; padding:0.75rem; }
.ml-stat-l { font-family:var(--font-m); font-size:0.58rem; color:var(--text-3); text-transform:uppercase; letter-spacing:0.08em; }
.ml-stat-v { font-family:var(--font-h); font-size:1.2rem; font-weight:700; margin-top:2px; }

/* ── Warning custom ── */
.aa-warn {
  background: rgba(251,191,36,0.06);
  border: 1px solid rgba(251,191,36,0.2);
  border-radius: 8px;
  padding: 0.65rem 1rem;
  font-family: var(--font-m);
  font-size: 0.7rem;
  color: var(--amber);
  margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ── Plotly theme ──────────────────────────────────────────────────
PT = dict(
    template="plotly_dark",
    paper_bgcolor="#0a0c14",
    plot_bgcolor="#0a0c14",
    font=dict(family="DM Mono, monospace", color="#94a3b8", size=11),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.06)", zeroline=False),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.06)", zeroline=False),
    margin=dict(l=8, r=8, t=32, b=8),
)

# ── Cache ─────────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def load_quotes(tickers: tuple) -> Dict:
    from core.data_fetcher import data_fetcher
    return {t: data_fetcher.get_quote(t) for t in tickers}

@st.cache_data(ttl=300)
def load_history(ticker: str, days: int = 180) -> pd.DataFrame:
    from core.data_fetcher import data_fetcher
    return data_fetcher.get_history(ticker, days)

@st.cache_data(ttl=120)
def scan_market() -> pd.DataFrame:
    from core.data_fetcher import data_fetcher
    return data_fetcher.scan_opportunities(top_n=15)

@st.cache_data(ttl=90)
def get_ta(ticker: str) -> Dict:
    from core.data_fetcher import data_fetcher
    from strategies.technical import technical_analyzer
    df = data_fetcher.get_history(ticker, 200)
    if df.empty: return {}
    r = technical_analyzer.analyze(df, ticker)
    return {"signal":r.signal,"ta_score":r.ta_score,"confidence":r.confidence,
            "reasons":r.reasons,"indicators":r.indicators}

@st.cache_data(ttl=600)
def get_ml(ticker: str) -> Dict:
    from core.data_fetcher import data_fetcher
    from strategies.ml_predictor import ml_predictor
    df = data_fetcher.get_history(ticker, 500)
    if df.empty: return {}
    if ml_predictor.needs_retraining(ticker):
        ml_predictor.train(df, ticker)
    p = ml_predictor.predict(df, ticker)
    return {"signal":p.signal,"proba":p.probability,"accuracy":p.model_accuracy,
            "features":p.features_used,"trained_at":p.trained_at}

@st.cache_data(ttl=300)
def get_backtest(ticker: str, strategy: str, days: int) -> Dict:
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

# ── Sidebar ───────────────────────────────────────────────────────
def render_sidebar() -> str:
    with st.sidebar:
        st.markdown("""
        <div style="padding:1.75rem 1.25rem 1rem;border-bottom:1px solid var(--border);margin-bottom:0.5rem">
          <div style="font-family:var(--font-h);font-size:1rem;font-weight:800;color:var(--teal);letter-spacing:0.12em">⬡ ALPHA ARENA</div>
          <div style="font-family:var(--font-m);font-size:0.6rem;color:var(--text-3);letter-spacing:0.08em;margin-top:3px">MERVAL · CEDEARS · PRO v2.0</div>
        </div>
        """, unsafe_allow_html=True)

        if "page" not in st.session_state:
            st.session_state["page"] = "Dashboard"

        pages = [("▦","Dashboard"),("◈","Scanner"),("◎","Análisis"),
                 ("⬡","ML Predictor"),("◷","Backtest"),("◻","Portfolio")]

        for icon, name in pages:
            is_active = st.session_state["page"] == name
            style = "background:var(--teal-dim);border:1px solid var(--teal-border);color:var(--teal)" if is_active else "border:1px solid transparent;color:var(--text-2)"
            if st.button(f"{icon}  {name}", key=f"nav_{name}", use_container_width=True):
                st.session_state["page"] = name
                st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="padding:0 0.75rem;font-family:var(--font-m);font-size:0.67rem;color:var(--text-2);line-height:2">
          <span class="sb-status">● {settings.trading_mode.upper()}</span><br>
          Capital: <span style="color:var(--text-1)">${settings.initial_capital:,.0f}</span><br>
          Universo: <span style="color:var(--text-1)">{len(settings.all_tickers)} activos</span><br>
          ML mín: <span style="color:var(--text-1)">{settings.ml_min_confidence:.0%}</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        if st.button("↺  Refrescar datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.markdown(f"""
        <div style="padding:0.75rem 0.75rem 0;font-family:var(--font-m);font-size:0.6rem;
                    color:var(--text-3);border-top:1px solid var(--border);margin-top:0.75rem">
          {datetime.now().strftime('%d/%m/%Y  %H:%M:%S')}
        </div>
        """, unsafe_allow_html=True)

    return st.session_state.get("page", "Dashboard")

# ── Pages ─────────────────────────────────────────────────────────

def page_header(title, subtitle):
    st.markdown(f"""
    <div class="aa-page-header">
      <div>
        <div class="aa-page-title">{title}</div>
        <div class="aa-page-sub">{subtitle}</div>
      </div>
      <div class="aa-timestamp">{datetime.now().strftime('%d %b %Y · %H:%M:%S')}</div>
    </div>
    """, unsafe_allow_html=True)


def page_dashboard():
    page_header("Mercado", "Cotizaciones en tiempo real · Yahoo Finance")
    tab1, tab2 = st.tabs(["▦  MERVAL", "◈  CEDEARs"])
    with tab1: _market_table(settings.merval_universe[:12], "MERVAL", "badge-violet")
    with tab2: _market_table(settings.cedear_universe, "CEDEAR", "badge-teal")


def _market_table(tickers, label, badge_cls):
    with st.spinner("Cargando..."):
        data = load_quotes(tuple(tickers))
    rows = [(t, q) for t, q in data.items() if q.get("ok")]
    if not rows:
        st.warning("Sin datos disponibles.")
        return

    st.markdown(f"""
    <div class="aa-card">
      <div class="aa-card-title">
        <span class="aa-badge {badge_cls}">{label}</span>
        {len(rows)} activos · {datetime.now().strftime('%H:%M:%S')}
      </div>
      <table class="aa-table">
        <thead>
          <tr>
            <th>Ticker</th>
            <th>Precio</th>
            <th>Cambio</th>
            <th>Máximo</th>
            <th>Mínimo</th>
            <th>Volumen</th>
          </tr>
        </thead>
        <tbody>
    """, unsafe_allow_html=True)

    for ticker, q in rows:
        chg = q['change']
        cls = "t-up" if chg > 0 else ("t-down" if chg < 0 else "t-flat")
        sign = "+" if chg > 0 else ""
        v = q['volume']
        vs = f"{v/1e6:.1f}M" if v > 1e6 else (f"{v/1e3:.0f}K" if v > 1000 else str(v))
        st.markdown(f"""
          <tr>
            <td><strong>{ticker.replace('.BA','')}</strong> <span style="color:var(--text-3);font-size:0.7rem">{ticker}</span></td>
            <td>${q['price']:,.2f}</td>
            <td class="{cls}">{sign}{chg:.2f}%</td>
            <td>${q['high']:,.2f}</td>
            <td>${q['low']:,.2f}</td>
            <td style="color:var(--text-2)">{vs}</td>
          </tr>
        """, unsafe_allow_html=True)

    st.markdown("</tbody></table></div>", unsafe_allow_html=True)


def page_scanner():
    page_header("Scanner", "Ranking dinámico · Momentum + Volumen + RSI + Tendencia")

    col1, col2 = st.columns([5, 1])
    with col2:
        if st.button("↺ Escanear", use_container_width=True):
            st.cache_data.clear()

    with st.spinner("Escaneando mercado..."):
        df = scan_market()

    if df.empty:
        st.warning("Sin resultados.")
        return

    def classify(rsi):
        if 25 < rsi < 45: return "BUY", "buy", "badge-teal", "var(--teal)"
        if rsi > 65:       return "SELL", "sell", "badge-red", "var(--red)"
        return "HOLD", "hold", "badge-amber", "var(--amber)"

    # Top 3
    st.markdown('<div class="aa-sec"><span class="aa-sec-title">Top Oportunidades</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="sc-grid">', unsafe_allow_html=True)

    for _, row in df.head(3).iterrows():
        lbl, cls, bcls, color = classify(row['rsi'])
        sp = int(row['score'] * 100)
        cc = "var(--teal)" if row['change'] >= 0 else "var(--red)"
        sg = "+" if row['change'] >= 0 else ""
        st.markdown(f"""
        <div class="sc {cls}">
          <div class="sc-head">
            <div>
              <div class="sc-sym">{row['ticker'].replace('.BA','')}</div>
              <div class="sc-mkt">{row['ticker']} · {row['market']}</div>
            </div>
            <span class="aa-badge {bcls}">{lbl}</span>
          </div>
          <div class="sc-price">${row['price']:,.2f} <span style="font-size:0.72rem;color:{cc};margin-left:6px">{sg}{row['change']:.2f}%</span></div>
          <div class="sc-grid2">
            <div class="sc-m"><div class="sc-ml">RSI</div><div class="sc-mv">{row['rsi']:.1f}</div></div>
            <div class="sc-m"><div class="sc-ml">Ret 20d</div><div class="sc-mv" style="color:{cc}">{"+" if row['ret_20d']>=0 else ""}{row['ret_20d']:.1f}%</div></div>
            <div class="sc-m"><div class="sc-ml">Vol ×</div><div class="sc-mv">{row['rel_volume']:.1f}x</div></div>
            <div class="sc-m"><div class="sc-ml">vs SMA50</div><div class="sc-mv">{"+" if row['vs_sma50_pct']>=0 else ""}{row['vs_sma50_pct']:.1f}%</div></div>
          </div>
          <div class="sc-bar">
            <div class="sc-bar-lbl"><span>Score</span><span style="color:{color};font-weight:500">{sp}%</span></div>
            <div class="sc-bar-track"><div class="sc-bar-fill" style="width:{sp}%;background:{color}"></div></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Tabla completa
    st.markdown(f'<div class="aa-sec"><span class="aa-sec-title">Ranking Completo</span><span class="aa-sec-count">{len(df)} activos</span></div>', unsafe_allow_html=True)

    disp = df[["ticker","market","price","change","score","rsi","ret_5d","ret_20d","rel_volume","vs_sma50_pct"]].copy()
    disp.columns = ["Ticker","Mercado","Precio","Cambio%","Score","RSI","Ret5d%","Ret20d%","Vol×","vsSMA50%"]

    def style_score(v):
        if isinstance(v, float) and 0 <= v <= 1:
            if v >= 0.6: return "background:#0d2818;color:#2dd4bf"
            if v >= 0.4: return "background:#1a1500;color:#fbbf24"
            return "background:#2d0a0a;color:#f87171"
        return ""

    def style_chg(v):
        if isinstance(v, (int, float)):
            return f"color:{'#2dd4bf' if v >= 0 else '#f87171'}"
        return ""

    styled = (disp.style
        .map(style_score, subset=["Score"])
        .map(style_chg, subset=["Cambio%","Ret5d%","Ret20d%","vsSMA50%"])
        .format({"Precio":"${:,.2f}","Cambio%":"{:+.2f}%","Score":"{:.0%}",
                 "RSI":"{:.0f}","Ret5d%":"{:+.1f}%","Ret20d%":"{:+.1f}%",
                 "Vol×":"{:.1f}x","vsSMA50%":"{:+.1f}%"}, na_rep="—"))
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # Scatter
    st.markdown('<div class="aa-sec"><span class="aa-sec-title">Score vs Retorno 20d</span></div>', unsafe_allow_html=True)
    df["Señal"] = df["rsi"].apply(lambda r: "BUY" if 25<r<45 else ("SELL" if r>65 else "HOLD"))
    fig = px.scatter(df, x="ret_20d", y="score", size="rel_volume", color="Señal",
        hover_data=["ticker","rsi","price"],
        color_discrete_map={"BUY":"#2dd4bf","SELL":"#f87171","HOLD":"#fbbf24"},
        labels={"ret_20d":"Retorno 20d (%)","score":"Score"})
    fig.add_vline(x=0, line_dash="dash", line_color="rgba(255,255,255,0.08)")
    fig.add_hline(y=0.5, line_dash="dash", line_color="rgba(255,255,255,0.08)")
    fig.update_layout(**PT, height=360)
    fig.update_traces(marker=dict(line=dict(width=0)))
    st.plotly_chart(fig, use_container_width=True)


def page_analysis():
    page_header("Análisis Técnico", "RSI · MACD · Bollinger · EMA20/50/200 · Stochastic · ADX")

    all_t = settings.merval_universe + settings.cedear_universe
    c1, c2, c3 = st.columns([3, 1, 1])
    with c1: ticker = st.selectbox("Activo", all_t)
    with c2: period = st.selectbox("Período", ["3M","6M","1A","2A"])
    with c3:
        st.write(""); st.write("")
        st.button("Analizar", use_container_width=True)

    days = {"3M":90,"6M":180,"1A":365,"2A":730}[period]

    with st.spinner("Cargando..."):
        df  = load_history(ticker, days)
        ta  = get_ta(ticker)

    if df.empty:
        st.warning(f"Sin datos para {ticker}")
        return

    if ta:
        sig = ta.get("signal","HOLD")
        sc  = ta.get("ta_score",0)
        cf  = ta.get("confidence",0)
        ind = ta.get("indicators",{})
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("Señal TA", sig, delta=f"Score {sc:+.2f}")
        c2.metric("Confianza", f"{cf:.0%}")
        c3.metric("RSI", f"{ind.get('rsi',50):.1f}")
        c4.metric("MACD Hist", f"{ind.get('macd_hist',0):.4f}")
        c5.metric("Precio", f"${df['Close'].iloc[-1]:,.2f}")

        if ta.get("reasons"):
            st.markdown(f"""
            <div class="aa-card" style="padding:0.6rem 1rem;margin:0.75rem 0">
              <span style="font-family:var(--font-m);font-size:0.7rem;color:var(--text-2)">
                {" &nbsp;·&nbsp; ".join(ta['reasons'])}
              </span>
            </div>
            """, unsafe_allow_html=True)

    from strategies.technical import TechnicalAnalyzer
    df_i = TechnicalAnalyzer.get_indicators_df(df)

    fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
        vertical_spacing=0.02, row_heights=[0.52,0.18,0.16,0.14],
        subplot_titles=[ticker,"MACD","RSI","Volumen"])

    fig.add_trace(go.Candlestick(x=df.index,open=df["Open"],high=df["High"],
        low=df["Low"],close=df["Close"],name="",showlegend=False,
        increasing=dict(line=dict(color="#2dd4bf"),fillcolor="rgba(45,212,191,0.75)"),
        decreasing=dict(line=dict(color="#f87171"),fillcolor="rgba(248,113,113,0.75)")),row=1,col=1)

    if "bb_upper" in df_i.columns:
        for cn,a in [("bb_upper",0.3),("bb_mid",0.55),("bb_lower",0.3)]:
            fig.add_trace(go.Scatter(x=df_i.index,y=df_i[cn],
                line=dict(color=f"rgba(129,140,248,{a})",width=1),showlegend=False),row=1,col=1)
        fig.add_trace(go.Scatter(
            x=list(df_i.index)+list(df_i.index[::-1]),
            y=list(df_i["bb_upper"])+list(df_i["bb_lower"][::-1]),
            fill="toself",fillcolor="rgba(129,140,248,0.04)",
            line=dict(color="rgba(0,0,0,0)"),showlegend=False),row=1,col=1)

    for ema,color in [("ema20","#fbbf24"),("ema50","#818cf8"),("ema200","rgba(248,113,113,0.65)")]:
        if ema in df_i.columns:
            fig.add_trace(go.Scatter(x=df_i.index,y=df_i[ema],
                line=dict(color=color,width=1.2),name=ema.upper()),row=1,col=1)

    if "macd" in df_i.columns:
        fig.add_trace(go.Scatter(x=df_i.index,y=df_i["macd"],line=dict(color="#2dd4bf",width=1.5),name="MACD"),row=2,col=1)
        fig.add_trace(go.Scatter(x=df_i.index,y=df_i["macd_signal"],line=dict(color="#fbbf24",width=1.5),name="Signal"),row=2,col=1)
        ch = ["#2dd4bf" if v>=0 else "#f87171" for v in df_i["macd_hist"].fillna(0)]
        fig.add_trace(go.Bar(x=df_i.index,y=df_i["macd_hist"],marker_color=ch,showlegend=False),row=2,col=1)

    if "rsi" in df_i.columns:
        fig.add_trace(go.Scatter(x=df_i.index,y=df_i["rsi"],
            line=dict(color="#818cf8",width=1.8),showlegend=False),row=3,col=1)
        fig.add_hline(y=70,line_dash="dot",line_color="rgba(248,113,113,0.4)",row=3,col=1)
        fig.add_hline(y=30,line_dash="dot",line_color="rgba(45,212,191,0.4)",row=3,col=1)
        fig.add_hrect(y0=30,y1=70,fillcolor="rgba(255,255,255,0.015)",line_width=0,row=3,col=1)

    vc = ["#2dd4bf" if c>=o else "#f87171" for c,o in zip(df["Close"],df["Open"])]
    fig.add_trace(go.Bar(x=df.index,y=df["Volume"],marker_color=vc,showlegend=False),row=4,col=1)

    fig.update_layout(**PT,height=820,xaxis_rangeslider_visible=False,
        legend=dict(orientation="h",y=1.02,font=dict(size=10)))
    st.plotly_chart(fig, use_container_width=True)


def page_ml():
    page_header("ML Predictor", "XGBoost · 30+ Features · Time-Series CV · Horizonte 5 días")

    all_t = settings.merval_universe + settings.cedear_universe
    c1, c2 = st.columns([3, 1])
    with c1: ticker = st.selectbox("Activo", all_t)
    with c2:
        st.write(""); st.write("")
        btn = st.button("⬡ Predecir", use_container_width=True)

    if not btn and "ml_ticker" not in st.session_state:
        st.markdown("""
        <div class="aa-card" style="padding:2.5rem;text-align:center">
          <div style="font-family:var(--font-h);font-size:1rem;color:var(--text-2);margin-bottom:0.4rem">Seleccioná un activo y presioná Predecir</div>
          <div style="font-family:var(--font-m);font-size:0.7rem;color:var(--text-3)">Primera vez tarda ~1 min — entrena con datos históricos reales</div>
        </div>
        """, unsafe_allow_html=True)
        return

    if btn:
        st.session_state["ml_ticker"] = ticker
    active = st.session_state.get("ml_ticker", ticker)

    with st.spinner(f"Entrenando modelo para {active}..."):
        res = get_ml(active)

    if not res:
        st.error("Datos insuficientes para este activo.")
        return

    sig   = res.get("signal","HOLD")
    proba = res.get("proba",0)
    acc   = res.get("accuracy",0)

    colors = {"BUY":("var(--teal)","rgba(45,212,191,0.06)","rgba(45,212,191,0.2)"),
              "SELL":("var(--red)","rgba(248,113,113,0.06)","rgba(248,113,113,0.2)"),
              "HOLD":("var(--amber)","rgba(251,191,36,0.06)","rgba(251,191,36,0.2)")}
    color, bg, border = colors.get(sig, colors["HOLD"])

    st.markdown(f"""
    <div class="ml-banner" style="background:{bg};border:1px solid {border}">
      <div>
        <div style="font-family:var(--font-m);font-size:0.58rem;color:var(--text-3);letter-spacing:0.12em;text-transform:uppercase;margin-bottom:4px">Predicción ML · {active}</div>
        <div class="ml-sig" style="color:{color}">{sig}</div>
      </div>
      <div class="ml-grid">
        <div class="ml-stat">
          <div class="ml-stat-l">Confianza</div>
          <div class="ml-stat-v" style="color:{color}">{proba:.0%}</div>
        </div>
        <div class="ml-stat">
          <div class="ml-stat-l">Accuracy CV</div>
          <div class="ml-stat-v" style="color:var(--text-1)">{acc:.1%}</div>
        </div>
        <div class="ml-stat">
          <div class="ml-stat-l">Features</div>
          <div class="ml-stat-v" style="color:var(--text-1)">{res.get('features',0)}</div>
        </div>
      </div>
    </div>
    <div class="aa-warn">⚠ Predicciones probabilísticas — siempre combinar con análisis técnico y gestión de riesgo</div>
    """, unsafe_allow_html=True)


def page_backtest():
    page_header("Backtest", "Sharpe · Sortino · Max Drawdown · Win Rate · Profit Factor")

    all_t = settings.merval_universe + settings.cedear_universe
    c1,c2,c3,c4 = st.columns(4)
    with c1: ticker = st.selectbox("Activo", all_t)
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
        st.info("Configurá los parámetros y presioná Ejecutar.")
        return

    if run:
        with st.spinner("Ejecutando backtest..."):
            st.session_state["bt_result"] = get_backtest(ticker, strat, days)

    res = st.session_state.get("bt_result",{})
    if not res or "error" in res:
        st.error(res.get("error","Error ejecutando backtest."))
        return

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("Retorno Total", f"{res['total_return']:+.1f}%")
    c2.metric("Sharpe", f"{res['sharpe']:.2f}")
    c3.metric("Max DD", f"-{res['max_dd']:.1f}%")
    c4.metric("Win Rate", f"{res['win_rate']:.0%}")
    c5.metric("Trades", res['summary'].get('Total Trades','—'))
    c6.metric("Profit Factor", res['summary'].get('Profit Factor','—'))

    eq = res.get("equity")
    dd = res.get("drawdown")
    if eq is not None and not eq.empty:
        fig = make_subplots(rows=2,cols=1,shared_xaxes=True,vertical_spacing=0.04,row_heights=[0.70,0.30])
        fig.add_trace(go.Scatter(x=eq.index,y=eq.values,fill="tozeroy",
            line=dict(color="#2dd4bf",width=2),fillcolor="rgba(45,212,191,0.06)",name="Capital"),row=1,col=1)
        fig.add_hline(y=settings.initial_capital,line_dash="dot",line_color="rgba(255,255,255,0.12)",row=1,col=1)
        if dd is not None and not dd.empty:
            fig.add_trace(go.Scatter(x=dd.index,y=dd.values,fill="tozeroy",
                line=dict(color="#f87171",width=1.5),fillcolor="rgba(248,113,113,0.1)",name="Drawdown"),row=2,col=1)
        fig.update_layout(**PT,height=460)
        st.plotly_chart(fig, use_container_width=True)

    trades = res.get("trades",[])
    if trades:
        st.markdown(f'<div class="aa-sec"><span class="aa-sec-title">Historial — {min(50,len(trades))} trades</span></div>', unsafe_allow_html=True)
        rows = [{"Entrada":t.entry_date[:10],"Salida":t.exit_date[:10],"Lado":t.side,
                 "$ Entrada":round(t.entry_price,2),"$ Salida":round(t.exit_price,2),
                 "P&L $":round(t.pnl,2),"P&L %":round(t.pnl_pct,2)} for t in trades[-50:]]
        df_t = pd.DataFrame(rows)
        styled = df_t.style.map(
            lambda v: f"color:{'#2dd4bf' if v>=0 else '#f87171'}" if isinstance(v,(int,float)) else "",
            subset=["P&L $","P&L %"])
        st.dataframe(styled, use_container_width=True, hide_index=True)


def page_portfolio():
    page_header("Portfolio", "Paper trading · Posiciones abiertas · Historial")

    try:
        from core.database import db
        async def _get():
            await db.initialize()
            return await db.get_open_trades(), await db.get_recent_trades(50), await db.get_trade_stats()

        with st.spinner(""):
            open_t, recent_t, stats = asyncio.run(_get())

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("P&L Total",   f"${stats['total_pnl']:,.2f}")
        c2.metric("Win Rate",    f"{stats['win_rate']:.0%}")
        c3.metric("Trades",      str(stats['closed_trades']))
        c4.metric("Mejor Trade", f"${stats['best_trade']:,.2f}")

        st.markdown('<hr>', unsafe_allow_html=True)
        st.markdown('<div class="aa-sec"><span class="aa-sec-title">Posiciones Abiertas</span></div>', unsafe_allow_html=True)

        if open_t:
            rows = [{"Ticker":t.ticker,"Lado":t.side,"Entrada":round(t.entry_price,2),
                     "Qty":t.quantity,"Stop":round(t.stop_loss or 0,2),
                     "Target":round(t.take_profit or 0,2),"Score":round(t.signal_score or 0,2),
                     "Fecha":str(t.entry_time)[:16]} for t in open_t]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.markdown("""
            <div class="aa-card" style="text-align:center;padding:2rem">
              <span style="font-family:var(--font-m);font-size:0.75rem;color:var(--text-3)">
                Sin posiciones abiertas · Iniciá el bot con <code>python main.py</code>
              </span>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error: {e}")


def main():
    page = render_sidebar()
    dispatch = {
        "Dashboard":    page_dashboard,
        "Scanner":      page_scanner,
        "Análisis":     page_analysis,
        "ML Predictor": page_ml,
        "Backtest":     page_backtest,
        "Portfolio":    page_portfolio,
    }
    dispatch.get(page, page_dashboard)()

if __name__ == "__main__":
    main()
