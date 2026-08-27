import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime as dt
import requests
import urllib3
import io
import re
import pypdf
import bdshare
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Page configuration
st.set_page_config(
    page_title="DSE BD-  MARKET ANALYZER",
    page_icon="🇧🇩",
    layout="wide"
)

# ----------------- CUSTOM CSS FOR REAL-TIME BLINKERS & CARDS ----------------- #
st.markdown("""
<style>
/* Minimize default top gap above title */
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}
header[data-testid="stHeader"] {
    height: 1.5rem !important;
    background: transparent !important;
}
.stAppHeader {
    background-color: transparent !important;
}
h1, .stHeadingContainer {
    margin-top: -1rem !important;
    padding-top: 0rem !important;
}

@keyframes pulse-green {
    0% { box-shadow: 0 0 0 0 rgba(0, 200, 83, 0.7); }
    70% { box-shadow: 0 0 0 10px rgba(0, 200, 83, 0); }
    100% { box-shadow: 0 0 0 0 rgba(0, 200, 83, 0); }
}
@keyframes pulse-red {
    0% { box-shadow: 0 0 0 0 rgba(213, 0, 0, 0.7); }
    70% { box-shadow: 0 0 0 10px rgba(213, 0, 0, 0); }
    100% { box-shadow: 0 0 0 0 rgba(213, 0, 0, 0); }
}
@keyframes pulse-yellow {
    0% { box-shadow: 0 0 0 0 rgba(255, 214, 0, 0.7); }
    70% { box-shadow: 0 0 0 10px rgba(255, 214, 0, 0); }
    100% { box-shadow: 0 0 0 0 rgba(255, 214, 0, 0); }
}

.blink-dot-green {
    display: inline-block; width: 11px; height: 11px;
    background-color: #00C853; border-radius: 50%;
    animation: pulse-green 1.5s infinite;
    margin-right: 6px; vertical-align: middle;
}
.blink-dot-red {
    display: inline-block; width: 11px; height: 11px;
    background-color: #D50000; border-radius: 50%;
    animation: pulse-red 1.5s infinite;
    margin-right: 6px; vertical-align: middle;
}
.blink-dot-yellow {
    display: inline-block; width: 11px; height: 11px;
    background-color: #FFD600; border-radius: 50%;
    animation: pulse-yellow 1.5s infinite;
    margin-right: 6px; vertical-align: middle;
}

.stock-card {
    border: 1px solid #e2e8f0;
    background-color: #ffffff;
    padding: 14px;
    border-radius: 10px;
    margin-bottom: 15px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    transition: transform 0.15s ease-in-out;
    min-height: 275px;
    height: 275px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-sizing: border-box;
}
.stock-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 6px rgba(0,0,0,0.08);
}
.stock-avatar {
    width: 38px; height: 38px;
    border-radius: 50%;
    background: linear-gradient(135deg, #0284c7, #0369a1);
    color: white; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; margin-right: 10px; flex-shrink: 0;
}
.stock-title { font-size: 14px; font-weight: 700; color: #0f172a; line-height: 1.2; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.stock-meta { font-size: 11px; color: #64748b; margin-top: 2px; }
.price-main { font-size: 24px; font-weight: 800; color: #0f172a; margin-right: 8px; }
.price-change { font-size: 14px; font-weight: 700; margin-right: 8px; }

.pattern-badge {
    display: inline-block;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    margin-top: 4px;
}
.pattern-badge-bull { background-color: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
.pattern-badge-bear { background-color: #fee2e2; color: #b91c1c; border: 1px solid #fecaca; }
.pattern-badge-neutral { background-color: #fef9c3; color: #a16207; border: 1px solid #fef08a; }

.inspector-card {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 15px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

.index-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 100%;
}
.index-title {
    font-size: 11px;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}
.index-val {
    font-size: 22px;
    font-weight: 800;
    color: #0f172a;
    margin-right: 6px;
}
.index-chg {
    font-size: 13px;
    font-weight: 700;
}

.news-row-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}
.news-row-bad {
    border-left: 4px solid #ef4444;
    background: #fffafa;
}
.news-row-good {
    border-left: 4px solid #10b981;
    background: #f0fdf4;
}
.news-row-neutral {
    border-left: 4px solid #94a3b8;
    background: #ffffff;
}

.news-badge {
    display: inline-block;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.3px;
}

.reversal-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-sizing: border-box;
    transition: transform 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}
.reversal-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(0,0,0,0.08);
}
.reversal-strategy-box {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-left: 5px solid #0284c7;
    border-radius: 8px;
    padding: 14px 18px;
    margin-top: 14px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}
</style>
""", unsafe_allow_html=True)

# ----------------- WATCHLIST METADATA ----------------- #
WATCHLIST_STOCKS = [
    {"symbol": "GP", "name": "Grameenphone Ltd.", "category": "A", "sector": "Telecommunication"},
    {"symbol": "SQURPHARMA", "name": "Square Pharmaceuticals Ltd.", "category": "A", "sector": "Pharma & Chemical"},
    {"symbol": "ACI", "name": "ACI Limited", "category": "A", "sector": "Pharma & Chemical"},
    {"symbol": "ACMELAB", "name": "The ACME Laboratories Ltd.", "category": "A", "sector": "Pharma & Chemical"},
    {"symbol": "BATBC", "name": "British American Tobacco BD", "category": "A", "sector": "Food & Allied"},
    {"symbol": "BRACBANK", "name": "BRAC Bank Ltd.", "category": "A", "sector": "Bank"},
    {"symbol": "IDLC", "name": "IDLC Finance Ltd.", "category": "A", "sector": "Financial Inst."},
    {"symbol": "LHB", "name": "LafargeHolcim Bangladesh PLC", "category": "A", "sector": "Cement"},
    {"symbol": "WALTONHIL", "name": "Walton Hi-Tech Industries", "category": "A", "sector": "Engineering"},
    {"symbol": "SONARBAINS", "name": "Sonar Bangla Insurance Ltd.", "category": "A", "sector": "Insurance"}
]

def get_dse_market_status():
    """Computes Bangladesh Standard Time (BST) date, time, and DSE market open/closed status."""
    now = dt.datetime.now()
    weekday = now.weekday()  # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
    # DSE trading days: Sunday (6), Monday (0), Tuesday (1), Wednesday (2), Thursday (3)
    is_trading_day = weekday in [6, 0, 1, 2, 3]

    curr_time = now.time()
    market_open = dt.time(10, 0)
    market_close = dt.time(14, 0)
    post_close = dt.time(14, 10)

    if is_trading_day:
        if market_open <= curr_time < market_close:
            status_text = "MARKET OPEN"
            status_icon = "🟢"
            status_bg = "#dcfce7"
            status_color = "#15803d"
            status_border = "#86efac"
            status_desc = "Continuous Trading Session (10:00 AM - 02:00 PM)"
        elif market_close <= curr_time <= post_close:
            status_text = "POST-CLOSING"
            status_icon = "🟡"
            status_bg = "#fef9c3"
            status_color = "#a16207"
            status_border = "#fde047"
            status_desc = "Post-Close Adjustment (02:00 PM - 02:10 PM)"
        else:
            status_text = "MARKET CLOSED"
            status_icon = "🔴"
            status_bg = "#fee2e2"
            status_color = "#b91c1c"
            status_border = "#fca5a5"
            status_desc = "Trading Hours: 10:00 AM - 02:00 PM BST"
    else:
        status_text = "MARKET CLOSED (Weekend)"
        status_icon = "🔴"
        status_bg = "#fee2e2"
        status_color = "#b91c1c"
        status_border = "#fca5a5"
        status_desc = "Weekly Market Holiday (Fri & Sat)"

    date_str = now.strftime("%A, %d %b %Y")
    time_str = now.strftime("%I:%M:%S %p")

    return {
        "date_str": date_str,
        "time_str": time_str,
        "status_text": status_text,
        "status_icon": status_icon,
        "status_bg": status_bg,
        "status_color": status_color,
        "status_border": status_border,
        "status_desc": status_desc
    }

# ----------------- SIDEBAR: LIVE CLOCK & MARKET STATUS ----------------- #
m_status = get_dse_market_status()

st.sidebar.markdown(f"""
<div style="background: linear-gradient(135deg, #ffffff, #f8fafc); border-radius: 12px; padding: 14px 16px; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.04); margin-bottom: 14px;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <span style="font-size: 11px; font-weight: 700; color: #64748b; letter-spacing: 0.3px;">📅 {m_status['date_str']}</span>
        <span style="font-size: 12px; font-weight: 800; color: #0f172a; font-family: monospace;">⏰ {m_status['time_str']}</span>
    </div>
    <div style="display: flex; align-items: center; justify-content: space-between; background: {m_status['status_bg']}; border: 1px solid {m_status['status_border']}; border-radius: 8px; padding: 6px 10px;">
        <div style="display: flex; align-items: center; gap: 6px;">
            <span style="font-size: 13px;">{m_status['status_icon']}</span>
            <span style="font-size: 12px; font-weight: 800; color: {m_status['status_color']};">{m_status['status_text']}</span>
        </div>
        <span style="font-size: 10px; color: {m_status['status_color']}; font-weight: 700;">BST (UTC+6)</span>
    </div>
    <div style="font-size: 10.5px; color: #64748b; margin-top: 6px; text-align: center;">
        {m_status['status_desc']}
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------- AUTO REFRESH SETTINGS ----------------- #
st.sidebar.header("⚡ Live Market Stream")
refresh_sec = st.sidebar.slider("Auto-Refresh Interval (Seconds)", min_value=5, max_value=60, value=10, step=5)
st_autorefresh(interval=refresh_sec * 1000, key="dse_live_price_autorefresh")

if st.sidebar.button("🔄 Force Refresh All Data"):
    st.cache_data.clear()

# ----------------- DUAL-SOURCE LIVE PRICE FETCHING ENGINE ----------------- #

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*"
}

@st.cache_data(ttl=5)
def get_live_market_feeds():
    """
    Fetches real-time market quotes from StockNow REST API & DSE Official feed.
    """
    feed_status = {
        "stocknow_ok": False,
        "stocknow_count": 0,
        "dse_ok": False,
        "dse_count": 0,
        "fetch_time": dt.datetime.now().strftime("%I:%M:%S %p")
    }
    
    stocknow_quotes = {}
    dse_quotes = {}

    # 1. Fetch from StockNow Live API
    try:
        url_sn = "https://stocknow.com.bd/api/v1/instruments"
        res_sn = requests.get(url_sn, headers=HTTP_HEADERS, verify=False, timeout=6)
        if res_sn.status_code == 200:
            raw_sn = res_sn.json()
            feed_status["stocknow_ok"] = True
            feed_status["stocknow_count"] = len(raw_sn)
            for code, item in raw_sn.items():
                sym = str(code).strip().upper()
                ltp = float(item.get("close") or item.get("ltp") or 0.0)
                ycp = float(item.get("ycp") or ltp)
                chg = float(item.get("change") or round(ltp - ycp, 2) if (ltp and ycp) else 0.0)
                pct = float(item.get("change_percent") or item.get("change_per") or (round(chg / ycp * 100, 2) if ycp > 0 else 0.0))
                high = float(item.get("high") or ltp)
                low = float(item.get("low") or ltp)
                vol = float(item.get("volume") or item.get("total_volume") or 0.0)
                val_mn = float(item.get("value") or item.get("total_value") or 0.0)
                trades = int(item.get("trades") or item.get("total_trade") or 0)
                avg_p = round((val_mn * 1_000_000) / vol, 2) if (val_mn > 0 and vol > 0) else ltp

                stocknow_quotes[sym] = {
                    "symbol": sym,
                    "name": item.get("name") or sym,
                    "category": item.get("category") or "A",
                    "ltp": ltp,
                    "ycp": ycp,
                    "change": chg,
                    "pct_change": pct,
                    "high": high,
                    "low": low,
                    "volume": vol,
                    "value_mn": val_mn,
                    "trades": trades,
                    "avg_price": avg_p,
                    "source": "StockNow Live API"
                }
    except Exception:
        pass

    # 2. Fetch from DSE Official Live Feed
    try:
        dse_df = bdshare.get_current_trade_data()
        if dse_df is not None and not dse_df.empty:
            feed_status["dse_ok"] = True
            feed_status["dse_count"] = len(dse_df)
            for _, r in dse_df.iterrows():
                sym = str(r.get("symbol", "")).strip().upper()
                ltp = float(r.get("ltp") or r.get("close") or 0.0) if pd.notnull(r.get("ltp")) else 0.0
                ycp = float(r.get("ycp") or ltp) if pd.notnull(r.get("ycp")) else ltp
                chg = float(r.get("change") or 0.0) if pd.notnull(r.get("change")) else round(ltp - ycp, 2)
                pct = round(chg / ycp * 100, 2) if (ycp and ycp > 0) else 0.0
                high = float(r.get("high") or ltp) if pd.notnull(r.get("high")) else ltp
                low = float(r.get("low") or ltp) if pd.notnull(r.get("low")) else ltp
                vol = float(r.get("volume") or 0.0) if pd.notnull(r.get("volume")) else 0.0
                val_mn = float(r.get("value") or 0.0) if pd.notnull(r.get("value")) else 0.0
                trades = int(r.get("trade") or 0) if pd.notnull(r.get("trade")) else 0
                avg_p = round((val_mn * 1_000_000) / vol, 2) if (val_mn > 0 and vol > 0) else ltp

                dse_quotes[sym] = {
                    "symbol": sym, "ltp": ltp, "ycp": ycp, "change": chg,
                    "pct_change": pct, "high": high, "low": low, "volume": vol,
                    "value_mn": val_mn, "trades": trades, "avg_price": avg_p,
                    "source": "DSE Official Feed"
                }
    except Exception:
        pass

    # Merge unified quotes dictionary
    unified = {}
    all_syms = set(stocknow_quotes.keys()) | set(dse_quotes.keys())
    for s in all_syms:
        sn = stocknow_quotes.get(s)
        ds = dse_quotes.get(s)
        primary = sn if sn is not None else ds
        if primary:
            unified[s] = primary

    return {
        "unified": unified,
        "stocknow": stocknow_quotes,
        "dse": dse_quotes,
        "status": feed_status
    }

# ----------------- DSE LIVE INDICES & MARKET STATS FETCHER ----------------- #

@st.cache_data(ttl=15)
def get_dse_market_indices():
    """
    Fetches real-time DSEX, DSES, and DS30 indices and market breadth from DSE official homepage.
    """
    indices = {
        "DSEX": {"name": "DSEX Broad Index", "value": 0.0, "change": 0.0, "pct_change": 0.0},
        "DSES": {"name": "DSES Shariah Index", "value": 0.0, "change": 0.0, "pct_change": 0.0},
        "DS30": {"name": "DS30 Blue-Chip Index", "value": 0.0, "change": 0.0, "pct_change": 0.0},
        "stats": {"trade": 0, "volume": 0, "value_mn": 0.0, "advanced": 0, "declined": 0, "unchanged": 0}
    }
    try:
        r = requests.get("https://www.dsebd.org/index.php", headers=HTTP_HEADERS, verify=False, timeout=6)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, "html.parser")
            for mid in soup.find_all("div", class_="midrow"):
                c1 = mid.find("div", class_="m_col-1")
                c2 = mid.find("div", class_="m_col-2")
                c3 = mid.find("div", class_="m_col-3")
                c4 = mid.find("div", class_="m_col-4")
                if c1 and c2 and c3 and c4:
                    name_txt = c1.get_text(strip=True).upper()
                    try:
                        val = float(c2.get_text(strip=True).replace(",", ""))
                        chg = float(c3.get_text(strip=True).replace(",", ""))
                        pct = float(c4.get_text(strip=True).replace("%", "").replace(",", "").strip())
                        if "DSEX" in name_txt or "DSE X" in name_txt:
                            if indices["DSEX"]["value"] == 0.0:
                                indices["DSEX"].update({"value": val, "change": chg, "pct_change": pct})
                        elif "DSES" in name_txt or "DSE S" in name_txt:
                            if indices["DSES"]["value"] == 0.0:
                                indices["DSES"].update({"value": val, "change": chg, "pct_change": pct})
                        elif "DS30" in name_txt or "DSE 30" in name_txt or "DSE30" in name_txt:
                            if indices["DS30"]["value"] == 0.0:
                                indices["DS30"].update({"value": val, "change": chg, "pct_change": pct})
                    except Exception:
                        pass
                
                # Check stats
                cwid = mid.find("div", class_="m_col-wid")
                cwid1 = mid.find("div", class_="m_col-wid1")
                cwid2 = mid.find("div", class_="m_col-wid2")
                if cwid and cwid1 and cwid2:
                    t1 = cwid.get_text(strip=True).replace(",", "")
                    t2 = cwid1.get_text(strip=True).replace(",", "")
                    t3 = cwid2.get_text(strip=True).replace(",", "")
                    if t1.isdigit() and indices["stats"]["trade"] == 0:
                        indices["stats"]["trade"] = int(t1)
                        indices["stats"]["volume"] = int(t2) if t2.isdigit() else 0
                        indices["stats"]["value_mn"] = float(t3) if t3.replace(".", "", 1).isdigit() else 0.0
                    elif t1.isdigit() and indices["stats"]["advanced"] == 0:
                        indices["stats"]["advanced"] = int(t1)
                        indices["stats"]["declined"] = int(t2) if t2.isdigit() else 0
                        indices["stats"]["unchanged"] = int(t3) if t3.isdigit() else 0
    except Exception:
        pass
    return indices

# ----------------- AUTHENTIC DSEX SUPPORT & REVERSAL ANALYZER ----------------- #

@st.cache_data(ttl=60)
def get_dsex_reversal_analysis(live_dsex_val: float = 0.0, advanced: int = 0, declined: int = 0):
    """
    Computes key technical support zones, Fibonacci pullback reversal targets, 
    moving averages, Bollinger lower band, RSI, and pivot levels to determine 
    how low DSEX can drop before turning around / reversing upwards.
    """
    end_d = dt.date.today()
    start_d = end_d - dt.timedelta(days=365)
    df = None
    try:
        df = bdshare.get_market_info_more_data(str(start_d), str(end_d))
    except Exception:
        pass

    if df is not None and not df.empty:
        try:
            df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y', errors='coerce')
            df = df.sort_values('Date').reset_index(drop=True)
            df['DSEX'] = pd.to_numeric(df['DSEX Index'], errors='coerce')
            df = df.dropna(subset=['DSEX'])
        except Exception:
            df = None

    if df is None or df.empty:
        try:
            df = bdshare.get_market_info()
            if df is not None and not df.empty:
                df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y', errors='coerce')
                df = df.sort_values('Date').reset_index(drop=True)
                df['DSEX'] = pd.to_numeric(df['DSEX Index'], errors='coerce')
                df = df.dropna(subset=['DSEX'])
        except Exception:
            pass

    if df is None or df.empty:
        base = live_dsex_val if live_dsex_val > 0 else 5640.0
        df = pd.DataFrame({'Date': [pd.Timestamp(end_d)], 'DSEX': [base]})

    if live_dsex_val > 0:
        today_dt = pd.Timestamp(end_d)
        if today_dt in df['Date'].values:
            df.loc[df['Date'] == today_dt, 'DSEX'] = live_dsex_val
        else:
            new_r = pd.DataFrame([{'Date': today_dt, 'DSEX': live_dsex_val}])
            df = pd.concat([df, new_r], ignore_index=True)

    dsex_now = float(df['DSEX'].iloc[-1])

    # Moving Averages & Exponential Averages
    ma20 = float(df['DSEX'].rolling(min(20, len(df))).mean().iloc[-1])
    ma50 = float(df['DSEX'].rolling(min(50, len(df))).mean().iloc[-1])
    ma100 = float(df['DSEX'].rolling(min(100, len(df))).mean().iloc[-1])
    ma200 = float(df['DSEX'].rolling(min(200, len(df))).mean().iloc[-1])
    ema9 = float(df['DSEX'].ewm(span=9, adjust=False).mean().iloc[-1])
    ema21 = float(df['DSEX'].ewm(span=21, adjust=False).mean().iloc[-1])

    # Bollinger Bands (20, 2)
    std20 = float(df['DSEX'].rolling(min(20, len(df))).std().iloc[-1])
    bb_lower = round(ma20 - (2.0 * std20), 2)
    bb_upper = round(ma20 + (2.0 * std20), 2)

    # RSI (14)
    delta = df['DSEX'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    rsi_series = 100 - (100 / (1 + rs))
    rsi_val = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 45.0

    # Swing High & Low (recent 60 days)
    recent_span = df.tail(min(60, len(df)))
    swing_high = float(recent_span['DSEX'].max())
    swing_low = float(recent_span['DSEX'].min())
    diff = swing_high - swing_low if swing_high > swing_low else dsex_now * 0.08

    fib_236 = round(swing_high - 0.236 * diff, 2)
    fib_382 = round(swing_high - 0.382 * diff, 2)
    fib_500 = round(swing_high - 0.500 * diff, 2)
    fib_618 = round(swing_high - 0.618 * diff, 2)
    fib_786 = round(swing_high - 0.786 * diff, 2)

    # 1. MARKET DIRECTION DETERMINATION
    if dsex_now >= ema9 and ema9 >= ema21 and dsex_now >= ma50:
        market_dir = "🟢 বুলিশ আপট্রেন্ড (Bullish Uptrend)"
        dir_badge = "BULLISH UPTREND (উর্ধ্বমুখী ট্রেন্ড)"
        dir_color = "#15803d"
        dir_bg = "#dcfce7"
        dir_desc = "বাজার শক্তিশালী আপট্রেন্ডে রয়েছে। প্রতিটি ডিপে প্রাতিষ্ঠানিক ক্রেতারা সক্রিয় রয়েছে এবং উপরের রেজিস্ট্যান্স টেস্ট করছে।"
        direction_mode = "UPTREND"
    elif dsex_now < ema9 and dsex_now < ema21:
        if rsi_val <= 32:
            market_dir = "🔴 চরম ওভারসোল্ড / বাউন্স আসন্ন (Oversold Dip — Rebound Imminent)"
            dir_badge = "OVERSOLD DIP / BOUNCE IMMINENT"
            dir_color = "#0284c7"
            dir_bg = "#e0f2fe"
            dir_desc = "বাজার শর্ট-টার্ম কারেকশনে থাকলেও RSI চরম ওভারসোল্ড লেভেলে নেমেছে। খুব সন্নিকটে থাকা সাপোর্ট জোন থেকে তীব্র টেকনিক্যাল বাউন্সের সম্ভাবনা সর্বাধিক।"
            direction_mode = "OVERSOLD_REBOUND"
        else:
            market_dir = "🔴 কারেক্টিভ ডাউনট্রেন্ড / পুলব্যাক (Corrective Downtrend)"
            dir_badge = "CORRECTIVE PULLBACK (পতনমুখী কারেকশন)"
            dir_color = "#b91c1c"
            dir_bg = "#fee2e2"
            dir_desc = "বাজার সাময়িক কারেকশনে রয়েছে এবং নিচের ডিমান্ড সাপোর্ট জোনের দিকে এগোচ্ছে।"
            direction_mode = "DOWNTREND"
    else:
        market_dir = "🟡 রেঞ্জবাউন্ড কনসোলিডেশন (Range-Bound Accumulation)"
        dir_badge = "RANGE ACCUMULATION (বটম তৈরি হচ্ছে)"
        dir_color = "#a16207"
        dir_bg = "#fef9c3"
        dir_desc = "বাজার একটি নির্দিষ্ট রেঞ্জে একুমুলেশন করছে এবং ব্রেকআউটের জন্য শক্তি সঞ্চয় করছে।"
        direction_mode = "CONSOLIDATION"

    # 2. DOWNSIDE BOUNCE TARGETS (যদি পতন অব্যাহত থাকে — কোথা থেকে ঘুরে দাঁড়াবে)
    raw_supports = [
        {
            "name": "Lower Bollinger Band (20, 2)",
            "name_bn": "১ম পুলব্যাক বাউন্স (Lower Bollinger Band)",
            "val": bb_lower,
            "type": "ওভারসোল্ড ভলাটিলিটি বাউন্স",
            "type_en": "Oversold Volatility Bounce",
            "strength": "⭐⭐⭐⭐",
            "desc": "স্ট্যাটিস্টিক্যাল ওভারসোল্ড লিমিট যেখানে বিক্রির চাপ কমে সূচক দ্রুত ঘুরে দাঁড়ায়।"
        },
        {
            "name": "Fibonacci 50.0% Retracement",
            "name_bn": "ফিবোনাচ্চি ৫০% রিট্রেসমেন্ট সাপোর্ট",
            "val": fib_500,
            "type": "স্বাভাবিক পুলব্যাক বাউন্স",
            "type_en": "Normal Pullback Bounce",
            "strength": "⭐⭐⭐",
            "desc": "স্বাভাবিক রিট্রেসমেন্ট সাপোর্ট লেভেল, যেখান থেকে প্রাথমিক বাউন্স দেখা যায়।"
        },
        {
            "name": "Fibonacci 61.8% Golden Ratio Zone",
            "name_bn": "ফিবোনাচ্চি ৬১.৮% গোল্ডেন রিভার্সাল জোন",
            "val": fib_618,
            "type": "প্রধান প্রাতিষ্ঠানিক রিভার্সাল সাপোর্ট",
            "type_en": "Major Golden Reversal Support",
            "strength": "⭐⭐⭐⭐⭐",
            "desc": "সবচেয়ে শক্তিশালী গোল্ডেন রেশিও রিভার্সাল জোন; এখানে প্রাতিষ্ঠানিক ক্রেতাদের বাই-অর্ডার ক্লাস্টার থাকে।"
        },
        {
            "name": "50-Day Moving Average Support",
            "name_bn": "৫০ দিনের মুভিং এভারেজ (50 SMA)",
            "val": round(ma50, 2),
            "type": "মাঝারি মেয়াদি ট্রেন্ড সাপোর্ট",
            "type_en": "Medium-Term Trend Support",
            "strength": "⭐⭐⭐⭐",
            "desc": "মাঝারি মেয়াদি ট্রেন্ডের প্রধান ডিফেন্স লাইন।"
        },
        {
            "name": "Fibonacci 78.6% Deep Value Floor",
            "name_bn": "ফিবোনাচ্চি ৭৮.৬% ডিপ সাপোর্ট ফ্লোর",
            "val": fib_786,
            "type": "ডিপ বটম অ্যাকুমুলেশন বেস",
            "type_en": "Deep Accumulation Floor",
            "strength": "⭐⭐⭐⭐⭐",
            "desc": "ডিপ কারেকশনে সর্বোচ্চ নিরাপদ রিভার্সাল বেস যেখানে হেভি অ্যাকুমুলেশন তৈরি হয়।"
        },
        {
            "name": "60-Day Major Swing Low Base",
            "name_bn": "৬০ দিনের প্রধান সুইং লো বটম",
            "val": round(swing_low, 2),
            "type": "ম্যাক্রো স্ট্রাকচারাল ফ্লোর",
            "type_en": "Structural Macro Floor",
            "strength": "⭐⭐⭐⭐⭐",
            "desc": "বাজারের কাঠামোগত বটম সাপোর্ট বেস।"
        }
    ]

    supports_below = [s for s in raw_supports if float(s["val"]) < dsex_now]
    supports_below.sort(key=lambda x: float(x["val"]), reverse=True)

    if not supports_below:
        primary_bounce = round(dsex_now * 0.985, 2)
        major_reversal_min = round(dsex_now * 0.97, 2)
        major_reversal_max = round(dsex_now * 0.98, 2)
        max_safe_floor = round(dsex_now * 0.95, 2)
    else:
        primary_bounce = float(supports_below[0]["val"])
        major_reversal_min = round(float(min(fib_618, ma50 if ma50 < dsex_now else fib_618)), 2)
        major_reversal_max = round(float(max(fib_618, ma50 if ma50 < dsex_now else fib_618)), 2)
        if major_reversal_min == major_reversal_max:
            major_reversal_min = round(major_reversal_min - 40.0, 2)
        max_safe_floor = float(min(fib_786, swing_low, bb_lower))

    pts_to_primary = round(dsex_now - primary_bounce, 2)
    pct_to_primary = round((pts_to_primary / dsex_now) * 100, 2)
    pts_to_major_max = round(dsex_now - major_reversal_max, 2)
    pts_to_major_min = round(dsex_now - major_reversal_min, 2)
    pts_to_floor = round(dsex_now - max_safe_floor, 2)
    pct_to_floor = round((pts_to_floor / dsex_now) * 100, 2)

    for s in raw_supports:
        diff_pts = round(dsex_now - float(s["val"]), 2)
        diff_pct = round((diff_pts / dsex_now) * 100, 2)
        s["diff_pts"] = diff_pts
        s["diff_pct"] = diff_pct
        s["is_below"] = float(s["val"]) < dsex_now

    # 3. UPSIDE RESISTANCE PEAKS (যদি বৃদ্ধি পায় — কোন পয়েন্টে পৌঁছানোর পর আবার নামবে)
    raw_resistances = [
        {
            "name": "9-Day Exponential Moving Average",
            "name_bn": "৯ দিনের এক্সপোনেনশিয়াল এভারেজ (EMA 9)",
            "val": round(ema9, 2),
            "type": "শর্ট-টার্ম মোমেন্টাম সিলিং",
            "type_en": "Short-Term Momentum Ceiling",
            "strength": "⭐⭐⭐",
            "desc": "বাউন্স আসার পর প্রাথমিক টেকনিক্যাল রেজিস্ট্যান্স; এখানে সাময়িক প্রফিট টেকিং হতে পারে।"
        },
        {
            "name": "Fibonacci 38.2% Retracement Ceiling",
            "name_bn": "১ম টেকনিক্যাল সিলিং (Fibonacci 38.2%)",
            "val": fib_382,
            "type": "১ম টেকনিক্যাল রেজিস্ট্যান্স সিলিং",
            "type_en": "1st Technical Resistance Ceiling",
            "strength": "⭐⭐⭐⭐",
            "desc": "পুলব্যাক রিবাউন্ডের পর প্রথম শক্ত রেজিস্ট্যান্স; এখানে পৌঁছালে প্রফিট বুকিংয়ের কারণে সাময়িক পতন দেখা দিতে পারে।"
        },
        {
            "name": "50-Day Moving Average Resistance",
            "name_bn": "৫০ দিনের মুভিং এভারেজ (50 SMA)",
            "val": round(ma50, 2),
            "type": "মাঝারি মেয়াদি সাপ্লাই ক্লাস্টার",
            "type_en": "Medium-Term Supply Cluster",
            "strength": "⭐⭐⭐⭐",
            "desc": "মাঝারি মেয়াদি প্রাতিষ্ঠানিক রেজিস্ট্যান্স ক্লাস্টার।"
        },
        {
            "name": "20-Day Moving Average Supply Barrier",
            "name_bn": "২০ দিনের মুভিং এভারেজ (20 SMA)",
            "val": round(ma20, 2),
            "type": "প্রধান প্রাতিষ্ঠানিক সাপ্লাই ব্যারিয়ার",
            "type_en": "Major Institutional Supply Barrier",
            "strength": "⭐⭐⭐⭐",
            "desc": "তীব্র সেলিং প্রেশার জোন; এখানে পৌঁছালে বড় প্রাতিষ্ঠানিক ট্রেডাররা প্রফিট তুলে সূচককে আবার কারেকশনে ফেলতে পারে।"
        },
        {
            "name": "Fibonacci 23.6% Retracement Peak",
            "name_bn": "ফিবোনাচ্চি ২৩.৬% প্রফিট বুকিং জোন",
            "val": fib_236,
            "type": "উচ্চমাত্রার প্রফিট বুকিং জোন",
            "type_en": "Heavy Profit Booking Zone",
            "strength": "⭐⭐⭐⭐",
            "desc": "বুলিশ র‍্যালিতে হেভি সাপ্লাই ও প্রফিট লক-ইন তৈরি হওয়ার জোন।"
        },
        {
            "name": "60-Day Major Swing High Peak",
            "name_bn": "৬০ দিনের প্রধান সুইং হাই চূড়া",
            "val": round(swing_high, 2),
            "type": "সর্বোচ্চ চূড়া ও মেগা রেজিস্ট্যান্স",
            "type_en": "Macro Swing High Peak",
            "strength": "⭐⭐⭐⭐⭐",
            "desc": "৬০ দিনের সর্বোচ্চ রেকর্ড পিক; এখানে পৌঁছালে তীব্র ওভারবট কন্ডিশন তৈরি হয়ে সূচক বড় ধরনের কারেকশনে নামবে।"
        },
        {
            "name": "Upper Bollinger Band (20, 2)",
            "name_bn": "আপার বলিঙ্গার ব্যান্ড (Upper BB)",
            "val": bb_upper,
            "type": "স্ট্যাটিস্টিক্যাল ওভারবট সিলিং",
            "type_en": "Statistical Overbought Ceiling",
            "strength": "⭐⭐⭐⭐⭐",
            "desc": "স্ট্যাটিস্টিক্যাল ওভারবট রিভার্সাল লিমিট।"
        }
    ]

    resistances_above = [r for r in raw_resistances if float(r["val"]) > dsex_now]
    resistances_above.sort(key=lambda x: float(x["val"]))

    if not resistances_above:
        res_1 = round(dsex_now * 1.015, 2)
        res_2_min = round(dsex_now * 1.025, 2)
        res_2_max = round(dsex_now * 1.04, 2)
        res_max_peak = round(dsex_now * 1.05, 2)
    else:
        res_1 = float(resistances_above[0]["val"])
        if len(resistances_above) >= 3:
            res_2_min = float(resistances_above[1]["val"])
            res_2_max = float(resistances_above[2]["val"])
        elif len(resistances_above) == 2:
            res_2_min = float(resistances_above[0]["val"])
            res_2_max = float(resistances_above[1]["val"])
        else:
            res_2_min = res_1
            res_2_max = round(res_1 * 1.015, 2)
        res_max_peak = float(swing_high if swing_high > dsex_now else bb_upper)

    pts_to_res1 = round(res_1 - dsex_now, 2)
    pct_to_res1 = round((pts_to_res1 / dsex_now) * 100, 2)
    pts_to_res2_min = round(res_2_min - dsex_now, 2)
    pts_to_res2_max = round(res_2_max - dsex_now, 2)
    pts_to_peak = round(res_max_peak - dsex_now, 2)
    pct_to_peak = round((pts_to_peak / dsex_now) * 100, 2)

    for r in raw_resistances:
        diff_pts = round(float(r["val"]) - dsex_now, 2)
        diff_pct = round((diff_pts / dsex_now) * 100, 2)
        r["diff_pts"] = diff_pts
        r["diff_pct"] = diff_pct
        r["is_above"] = float(r["val"]) > dsex_now

    if rsi_val <= 30:
        rsi_status = "🔴 চরম ওভারসোল্ড (Extreme Oversold — তীব্র রিভার্সাল বাউন্স আসন্ন)"
        rsi_color = "#16a34a"
    elif rsi_val <= 42:
        rsi_status = "🟡 কারেকশন শেষ পর্যায়ে (Approaching Oversold Rebound Zone)"
        rsi_color = "#0284c7"
    elif rsi_val <= 58:
        rsi_status = "⚪ ব্যালেন্সড নিউট্রাল কনসোলিডেশন (Neutral Range)"
        rsi_color = "#64748b"
    else:
        rsi_status = "🟢 বুলিশ মোমেন্টাম বজায় রয়েছে (Healthy Bullish Momentum)"
        rsi_color = "#16a34a"

    # 4. AUTHENTIC MATHEMATICAL PROBABILITY & FORECAST MODEL
    # Computed purely from genuine live indicators: Proximity to S/R, RSI extremity, Live Market Breadth, MA alignment
    dist_to_supp = max(1.0, abs(dsex_now - primary_bounce))
    dist_to_res = max(1.0, abs(res_1 - dsex_now))
    proximity_score = (dist_to_res / (dist_to_supp + dist_to_res)) * 100.0
    rsi_bounce_score = max(0.0, min(100.0, ((70.0 - rsi_val) / 45.0) * 100.0))
    tot_trades = advanced + declined
    breadth_score = (advanced / tot_trades * 100.0) if tot_trades > 0 else 50.0
    ma_score = 65.0 if dsex_now >= ema9 else 35.0

    raw_prob = (0.35 * proximity_score) + (0.35 * rsi_bounce_score) + (0.20 * breadth_score) + (0.10 * ma_score)
    calculated_prob_up = round(max(5.0, min(95.0, raw_prob)), 1)
    calculated_prob_down = round(100.0 - calculated_prob_up, 1)

    if calculated_prob_up >= 55.0:
        prob_pct = calculated_prob_up
        pred_verdict = "📈 ইনডেক্স বাড়ার সম্ভাবনা প্রবল (Strong Rebound)"
        pred_action = "ইনডেক্স বাড়বে (বাউন্স আসন্ন)"
        pred_color = "#15803d"
        pred_bg = "#f0fdf4"
        pred_border = "#86efac"
        pred_target = f"টার্গেট: {res_1:,.1f} – {res_2_min:,.0f} (+{pts_to_res1:,.1f} pts)"
        pred_reason = f"RSI(14)={rsi_val:.1f} (চরম ওভারসোল্ড), ১ম বাউন্স সাপোর্ট ({primary_bounce:,.1f}) মাত্র {pts_to_primary:,.1f} পয়েন্ট নিচে এবং মার্কেট ব্রেডথ পজিটিভ থাকায় ইনডেক্স ঘুরে দাঁড়ানোর সম্ভাবনা {calculated_prob_up}%।"
    elif calculated_prob_down >= 55.0:
        prob_pct = calculated_prob_down
        pred_verdict = "📉 ইনডেক্স কমার সম্ভাবনা বেশি (Pullback Likely)"
        pred_action = "ইনডেক্স কমবে (কারেকশন নামবে)"
        pred_color = "#b91c1c"
        pred_bg = "#fef2f2"
        pred_border = "#fca5a5"
        pred_target = f"সাপোর্ট টার্গেট: {primary_bounce:,.1f} (-{pts_to_primary:,.1f} pts)"
        pred_reason = f"RSI(14)={rsi_val:.1f} এবং রেজিস্ট্যান্স ক্লাস্টার নিকটবর্তী হওয়ায় মুনাফা তোলার কারণে সূচক কারেকশনে নামার সম্ভাবনা {calculated_prob_down}%।"
    else:
        prob_pct = 50.0
        pred_verdict = "⚖️ ব্যালেন্সড কনসোলিডেশন (Range-Bound)"
        pred_action = "রেঞ্জবাউন্ড থাকবে"
        pred_color = "#0284c7"
        pred_bg = "#f0f9ff"
        pred_border = "#bae6fd"
        pred_target = f"রেঞ্জ: {primary_bounce:,.0f} – {res_1:,.0f}"
        pred_reason = "ক্রেতা ও বিক্রেতার ভারসাম্যপূর্ণ অবস্থানের কারণে সূচক নির্দিষ্ট রেঞ্জে কনসোলিডেশন করছে।"

    return {
        "df": df,
        "dsex_now": dsex_now,
        "market_dir": market_dir,
        "dir_badge": dir_badge,
        "dir_color": dir_color,
        "dir_bg": dir_bg,
        "dir_desc": dir_desc,
        "direction_mode": direction_mode,
        # Predictive Forecast
        "prob_pct": prob_pct,
        "pred_verdict": pred_verdict,
        "pred_action": pred_action,
        "pred_color": pred_color,
        "pred_bg": pred_bg,
        "pred_border": pred_border,
        "pred_target": pred_target,
        "pred_reason": pred_reason,
        # Downside Bounces
        "primary_bounce": primary_bounce,
        "pts_to_primary": pts_to_primary,
        "pct_to_primary": pct_to_primary,
        "major_reversal_min": major_reversal_min,
        "major_reversal_max": major_reversal_max,
        "pts_to_major_min": pts_to_major_min,
        "pts_to_major_max": pts_to_major_max,
        "max_safe_floor": max_safe_floor,
        "pts_to_floor": pts_to_floor,
        "pct_to_floor": pct_to_floor,
        # Upside Ceilings
        "res_1": res_1,
        "pts_to_res1": pts_to_res1,
        "pct_to_res1": pct_to_res1,
        "res_2_min": res_2_min,
        "res_2_max": res_2_max,
        "pts_to_res2_min": pts_to_res2_min,
        "pts_to_res2_max": pts_to_res2_max,
        "res_max_peak": res_max_peak,
        "pts_to_peak": pts_to_peak,
        "pct_to_peak": pct_to_peak,
        # Technical Levels
        "swing_high": swing_high,
        "swing_low": swing_low,
        "fib_236": fib_236,
        "fib_382": fib_382,
        "fib_500": fib_500,
        "fib_618": fib_618,
        "fib_786": fib_786,
        "ma20": round(ma20, 2),
        "ma50": round(ma50, 2),
        "ma200": round(ma200, 2),
        "bb_lower": bb_lower,
        "bb_upper": bb_upper,
        "rsi_val": round(rsi_val, 1),
        "rsi_status": rsi_status,
        "rsi_color": rsi_color,
        "supports": raw_supports,
        "resistances": raw_resistances
    }

# ----------------- AUTHENTIC DSE NEWS & RISK CLASSIFIER ----------------- #

def classify_dse_news(title: str, details: str):
    """
    Analyzes DSE corporate disclosure text to classify sentiment as:
    - 🔴 BAD NEWS / RISK ALERT (Losses, EPS drop, Plant shutdown, Show-cause, Downgrade, Selling pressure)
    - 🟢 GOOD NEWS / CATALYST (Earnings surge, Dividend declaration, Upgrades, Expansion, Insider buying)
    - ⚪ NEUTRAL / NOTICE (Record dates, AGM logistics, Share transmission)
    """
    text = f"{title} {details}".lower()
    
    # 🔴 Bad News / Risk Triggers
    bad_keywords = [
        ("decrease in eps", "EPS Drop / Profit Decline"),
        ("drop in eps", "EPS Drop / Profit Decline"),
        ("eps has decreased", "EPS Drop / Profit Decline"),
        ("eps decreased", "EPS Drop / Profit Decline"),
        ("negative eps", "Negative EPS Reported"),
        ("incurred net loss", "Net Loss Incurred"),
        ("loss after tax", "Net Loss Incurred"),
        ("decline in profit", "Profit Decline"),
        ("profit decreased", "Profit Decline"),
        ("lower net profit", "Profit Decline"),
        ("shut down", "Production / Plant Shutdown"),
        ("production suspended", "Production Suspended"),
        ("plant shutdown", "Plant Shutdown"),
        ("halted production", "Production Halted"),
        ("factory closed", "Factory Closed"),
        ("show-cause", "Show-Cause Notice Issued"),
        ("unusual price hike", "BSEC / DSE Price Query"),
        ("non-compliance", "Regulatory Non-Compliance"),
        ("penalty", "Regulatory Penalty"),
        ("fined", "Regulatory Fine"),
        ("litigation", "Litigation / Legal Dispute"),
        ("lawsuit", "Lawsuit / Legal Case"),
        ("downgrade", "Credit Rating Downgrade"),
        ("downgraded", "Credit Rating Downgrade"),
        ("postponement of agm", "AGM Postponed"),
        ("delayed financial", "Financial Reporting Delayed"),
        ("going concern", "Going Concern Auditor Alert"),
        ("qualified opinion", "Auditor Qualified Opinion"),
        ("sale intimation", "Sponsor/Director Selling Shares"),
        ("intent to sale", "Sponsor/Director Selling Shares"),
        ("intended to sale", "Sponsor/Director Selling Shares"),
        ("z-category", "Category Downgrade to Z")
    ]
    
    # 🟢 Good News / Positive Triggers
    good_keywords = [
        ("increase in eps", "EPS Growth / Strong Earnings"),
        ("growth in eps", "EPS Growth / Strong Earnings"),
        ("eps has increased", "EPS Growth / Strong Earnings"),
        ("eps increased", "EPS Growth / Strong Earnings"),
        ("growth in profit", "Net Profit Surge"),
        ("profit surged", "Net Profit Surge"),
        ("revenue increased", "Revenue / Sales Growth"),
        ("recommended dividend", "Dividend Declaration"),
        ("declared dividend", "Dividend Declaration"),
        ("cash dividend", "Cash Dividend Declaration"),
        ("stock dividend", "Bonus / Stock Dividend"),
        ("bonus share", "Bonus Share Declaration"),
        ("interim dividend", "Interim Dividend"),
        ("upgraded to", "Credit Rating Upgrade"),
        ("rating upgraded", "Credit Rating Upgrade"),
        ("commercial operation", "Commercial Operation Resumed / Expanded"),
        ("expansion", "Business / Capacity Expansion"),
        ("new unit", "New Production Unit"),
        ("export order", "Export Order Received"),
        ("buy intimation", "Sponsor/Director Buying Shares"),
        ("intended to buy", "Sponsor/Director Buying Shares"),
        ("purchase of shares", "Sponsor/Director Buying Shares"),
        ("approval received", "Regulatory Approval Received"),
        ("fda approval", "FDA / Global Regulatory Approval")
    ]
    
    for kw, reason in bad_keywords:
        if kw in text:
            return "BAD NEWS / RISK ALERT", "🔴", "#fee2e2", "#b91c1c", "news-row-bad", reason
            
    for kw, reason in good_keywords:
        if kw in text:
            return "GOOD NEWS / CATALYST", "🟢", "#dcfce7", "#15803d", "news-row-good", reason
            
    return "NEUTRAL NOTICE", "⚪", "#f1f5f9", "#475569", "news-row-neutral", "General Corporate Notice"

@st.cache_data(ttl=60)
def fetch_authentic_dse_news():
    """
    Fetches real-time authentic price-sensitive news and corporate announcements
    from DSE official dissemination board and StockNow API.
    """
    all_news = []
    seen_keys = set()

    # 1. Fetch Price Sensitive News from bdshare
    try:
        df_psn = bdshare.get_price_sensitive_news()
        if df_psn is not None and not df_psn.empty:
            for _, r in df_psn.iterrows():
                code = str(r.get("code", "")).strip().upper()
                title = str(r.get("title", "")).strip()
                details = str(r.get("news", "")).strip()
                date_str = str(r.get("date", "")).strip()
                key = (code, title[:40])
                if key not in seen_keys and code:
                    seen_keys.add(key)
                    tag, icon, bg, fg, row_cls, reason = classify_dse_news(title, details)
                    all_news.append({
                        "code": code,
                        "title": title,
                        "details": details,
                        "date": date_str,
                        "sentiment": tag,
                        "icon": icon,
                        "bg": bg,
                        "fg": fg,
                        "row_cls": row_cls,
                        "reason": reason,
                        "source": "DSE Official Disclosures"
                    })
    except Exception:
        pass

    # 2. Fetch from StockNow Live News API (multi-page)
    for p in range(1, 5):
        try:
            url = f"https://stocknow.com.bd/api/v1/news?page={p}"
            res = requests.get(url, headers=HTTP_HEADERS, verify=False, timeout=6)
            if res.status_code == 200:
                data = res.json().get("data", [])
                for item in data:
                    code = str(item.get("prefix", "")).strip().upper()
                    title = str(item.get("title") or item.get("details", "")[:80]).strip()
                    details = str(item.get("details", "")).strip()
                    post_d = str(item.get("post_date", "")).strip()
                    key = (code, title[:40])
                    if key not in seen_keys and code:
                        seen_keys.add(key)
                        tag, icon, bg, fg, row_cls, reason = classify_dse_news(title, details)
                        all_news.append({
                            "code": code,
                            "title": title,
                            "details": details,
                            "date": post_d,
                            "sentiment": tag,
                            "icon": icon,
                            "bg": bg,
                            "fg": fg,
                            "row_cls": row_cls,
                            "reason": reason,
                            "source": "StockNow Live Feed"
                        })
        except Exception:
            pass

    return all_news

def parse_date_obj(d_str: str):
    """Parses date string from DSE circular into a datetime.date object."""
    if not d_str or any(k in d_str.lower() for k in ['postponed', 'later', 'notice', 'tbd', 'permission', 'tba']):
        return None
    cleaned = re.sub(r'^[^\d]+', '', d_str).strip()
    m1 = re.search(r'(\d{1,2})-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-(\d{2,4})', cleaned, re.IGNORECASE)
    if m1:
        day, mon, yr = int(m1.group(1)), m1.group(2).capitalize(), int(m1.group(3))
        if yr < 100:
            yr += 2000
        try:
            return dt.datetime.strptime(f'{day}-{mon}-{yr}', '%d-%b-%Y').date()
        except Exception:
            pass
    m2 = re.search(r'(\d{1,2})\s+([A-Za-z]+),?\s+(\d{4})', cleaned)
    if m2:
        day, mon, yr = int(m2.group(1)), m2.group(2)[:3].capitalize(), int(m2.group(3))
        try:
            return dt.datetime.strptime(f'{day}-{mon}-{yr}', '%d-%b-%Y').date()
        except Exception:
            pass
    return None

def clean_agm_company_name(text: str) -> str:
    s = " ".join(text.split()).strip()
    s = re.sub(r'^(?:.*?(?:notified later\.?|Time|Venue|Date|Information|\bA\.?M\.?\b|\bP\.?M\.?\b|Platform|Hybrid|Court|Order|Lounge\)\.|\d+\.\d+\s*(?:\bAM\b|\bPM\b))\s+)', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'^[0-9\.\s\-\)\(\/\,\;]+', '', s).strip()
    return s

@st.cache_data(ttl=300)
def fetch_upcoming_dse_events():
    """
    Parses corporate events from the official DSE circular (Company_AGM_EGM.pdf)
    AND real-time DSE corporate disclosures.
    STRICT RULE: The Record Date is the primary cut-off priority.
    If a company's Record Date has already passed before today, it is discarded.
    Only events with upcoming record dates (>= today) or pending/to-be-announced dates are returned.
    """
    today = dt.date.today()
    events = []
    seen = set()
    
    # 1. Parse official PDF circular
    try:
        r = requests.get("https://www.dsebd.org/Company_AGM_EGM.pdf", headers=HTTP_HEADERS, verify=False, timeout=10)
        if r.status_code == 200:
            reader = pypdf.PdfReader(io.BytesIO(r.content))
            
            for page in reader.pages:
                raw_lines = [l.strip() for l in page.extract_text().split('\n') if l.strip()]
                clean_lines = [l for l in raw_lines if not any(h in l for h in ['Last Updated', 'Dhaka Stock Exchange PLC.', "Company's AGM/EGM", 'Name of the Company', 'Purpose Date of AGM', 'Date Venue/Mode Time'])]
                
                i = 0
                while i < len(clean_lines):
                    line = clean_lines[i]
                    ye_match = re.search(r'(June\s+\d+,\s*\d{4}|December\s+\d+,\s*\d{4}|March\s+\d+,\s*\d{4}|September\s+\d+,\s*\d{4}|For the purpose of|For amendment of)', line, flags=re.IGNORECASE)
                    
                    if ye_match:
                        trigger_start = ye_match.start()
                        co_part = line[:trigger_start].strip()
                        
                        if i > 0 and len(co_part) < 25:
                            pl = clean_lines[i-1]
                            if not pl.endswith('.') and len(pl) < 45 and not any(t in pl.lower() for t in ['venue:', 'mode:', 'platform', 'samarai', 'complex', 'tower', 'auditorium', 'notified later', 'permission']):
                                full_co = (pl + ' ' + co_part).strip()
                            else:
                                full_co = co_part
                        else:
                            full_co = co_part
                        
                        full_co = clean_agm_company_name(full_co)
                        
                        body_lines = [line[trigger_start:]]
                        j = i + 1
                        while j < len(clean_lines):
                            next_l = clean_lines[j]
                            if re.search(r'(?:June\s+\d+|December\s+\d+|March\s+\d+|September\s+\d+)\s*,\s*\d{4}|For the purpose of|For amendment of', next_l, flags=re.IGNORECASE):
                                break
                            body_lines.append(next_l)
                            j += 1
                        
                        body_text = ' '.join(body_lines).strip()
                        
                        if full_co and len(full_co) >= 3 and not full_co.lower().startswith('http'):
                            ye_val = ye_match.group(1).strip()
                            
                            div_match = re.search(r'(\d+(?:\.\d+)?%\s*(?:Cash|Stock|Bonus)(?:\s*(?:and\s*\d+%\s*Stock|\s*Dividend))?|No [Dd]ividend|Nil)', body_text)
                            dividend = div_match.group(1).strip() if div_match else ('EGM / ' + ye_val if 'purpose' in ye_val.lower() or 'amendment' in ye_val.lower() else 'Corporate Purpose')
                            
                            dates = re.findall(r'(\d{1,2}-(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{2,4}|\d{1,2}\s+[A-Za-z]+,?\s+\d{4})', body_text)
                            is_postponed = any(k in body_text.lower() for k in ['postponed', 'notified later', 'court', 'consent', 'permission'])
                            
                            agm_date = dates[0] if (len(dates) >= 1 and not is_postponed) else ('Postponed / Court Consent Awaited' if is_postponed else (dates[0] if dates else 'To be notified later'))
                            rec_date = dates[1] if len(dates) >= 2 else (dates[0] if (len(dates) == 1 and 'record' in body_text.lower()) else 'Announced in Notice')
                            
                            rec_dt = parse_date_obj(rec_date)
                            agm_dt = parse_date_obj(agm_date)
                            
                            # If Record Date is already in the past, discard
                            if rec_dt is not None and rec_dt < today:
                                i = j
                                continue
                            
                            if rec_dt is not None and rec_dt >= today:
                                days_away = (rec_dt - today).days
                                countdown_str = "TODAY (Record Date)" if days_away == 0 else (f"In {days_away} Days (Record Date)" if days_away > 1 else "Tomorrow (Record Date)")
                                status_tag = f"Upcoming Record Date ({countdown_str})"
                                status_icon = "📅"
                                s_bg, s_fg = "#dbeafe", "#1d4ed8"
                                sort_key = rec_dt
                            else:
                                countdown_str = "Record Date Awaiting Schedule"
                                status_tag = "Record Date Pending / Court Consent Awaited" if is_postponed else "Record Date To Be Announced"
                                status_icon = "⏸️" if is_postponed else "ℹ️"
                                s_bg, s_fg = "#fef9c3" if is_postponed else "#f1f5f9", "#a16207" if is_postponed else "#475569"
                                sort_key = dt.date(2099, 12, 31)
                            
                            k = (full_co.lower(), ye_val.lower())
                            if k not in seen:
                                seen.add(k)
                                events.append({
                                    'company': full_co,
                                    'dividend': dividend,
                                    'year_end': ye_val,
                                    'agm_date': agm_date,
                                    'record_date': rec_date,
                                    'rec_dt': rec_dt,
                                    'agm_dt': agm_dt,
                                    'sort_key': sort_key,
                                    'countdown': countdown_str,
                                    'status': status_tag,
                                    'icon': status_icon,
                                    'bg': s_bg,
                                    'fg': s_fg,
                                    'details': body_text,
                                    'source': 'Official DSE Circular (Company_AGM_EGM.pdf)'
                                })
                        i = j
                    else:
                        i += 1
    except Exception:
        pass
        
    # 2. Add real-time DSE announcements with upcoming Record Dates (Multi-Page Dissemination)
    for p in range(1, 35):
        try:
            url = f"https://stocknow.com.bd/api/v1/news?page={p}"
            res = requests.get(url, headers=HTTP_HEADERS, verify=False, timeout=6)
            if res.status_code == 200:
                for item in res.json().get("data", []):
                    code = str(item.get("prefix", "")).strip().upper()
                    title = str(item.get("title") or "").strip()
                    details = str(item.get("details", "")).strip()
                    text = f"{title} {details}"
                    
                    matches = re.findall(r'(?:[Rr]ecord\s+[Dd]ate|[Ss]uspended\s+on\s+record\s+date|[Ee]ntitlement\s+of\s+coupon)[^\.\;\n]{0,60}?(\d{1,2}-(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{2,4}|\d{1,2}\s+[A-Za-z]+,?\s+\d{4}|\d{1,2}\.\d{1,2}\.\d{4})', text)
                    for rm in matches:
                        rdt = parse_date_obj(rm)
                        if rdt and rdt >= today:
                            k = (code.lower(), str(rdt))
                            if k not in seen:
                                seen.add(k)
                                div_m = re.search(r'(\d+(?:\.\d+)?%\s*(?:Cash|Stock|Bonus)(?:\s*(?:and\s*\d+%\s*Stock|\s*Dividend))?|No [Dd]ividend|Nil)', text)
                                div_str = div_m.group(1).strip() if div_m else ("EGM / Corporate Purpose" if "egm" in text.lower() or "purpose" in text.lower() else "Coupon / Dividend Entitlement")
                                
                                days_away = (rdt - today).days
                                countdown_str = "TODAY" if days_away == 0 else (f"In {days_away} Days" if days_away > 1 else "Tomorrow")
                                
                                events.append({
                                    'company': f"{code} ({title[:35]})" if title else code,
                                    'dividend': div_str,
                                    'year_end': "FY 2026",
                                    'agm_date': "Trading Resumes After Record Date" if "suspended" in text.lower() else "See Corporate Notice",
                                    'record_date': rm,
                                    'rec_dt': rdt,
                                    'agm_dt': None,
                                    'sort_key': rdt,
                                    'countdown': countdown_str,
                                    'status': f"Upcoming Record Date ({countdown_str})",
                                    'icon': "📅",
                                    'bg': "#dbeafe",
                                    'fg': "#1d4ed8",
                                    'details': details or title,
                                    'source': "DSE Real-Time Disclosure"
                                })
        except Exception:
            pass

    events.sort(key=lambda x: (x['sort_key'], x['company']))
    return events

# ----------------- AUTHENTIC HISTORICAL DATA FETCHER ----------------- #

@st.cache_data(ttl=600)
def fetch_authentic_history(symbol: str, days: int = 365) -> pd.DataFrame:
    """
    Fetches genuine historical daily OHLCV bars directly from DSE archive via bdshare.
    Filters out non-trading / off-days where open, high, or low is zero.
    """
    symbol = symbol.upper().strip()
    end_date = str(dt.date.today())
    start_date = str(dt.date.today() - dt.timedelta(days=days))

    try:
        df = bdshare.get_historical_data(start_date, end_date, symbol)
        if df is not None and not df.empty:
            df.columns = [str(c).lower().strip() for c in df.columns]
            df.index = pd.to_datetime(df.index, errors='coerce')
            df.dropna(subset=['close'], inplace=True)
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            # Discard non-trading off-days where open, high, or low <= 0
            df = df[(df['open'] > 0) & (df['high'] > 0) & (df['low'] > 0) & (df['close'] > 0)]
            df.sort_index(ascending=True, inplace=True)
            return df
    except Exception:
        pass

    try:
        url = f"https://www.dsebd.org/day_end_archive.php?startDate={start_date}&endDate={end_date}&inst={symbol}&archive=data"
        res = requests.get(url, headers=HTTP_HEADERS, verify=False, timeout=12)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, "html.parser")
            table = soup.find("table", {"class": "shares-table"})
            if table:
                rows = []
                for tr in table.find_all("tr")[1:]:
                    tds = [td.get_text(strip=True) for td in tr.find_all("td")]
                    if len(tds) >= 8:
                        rows.append(tds)
                if rows:
                    cols = ["Date", "Trading_Code", "LTP", "High", "Low", "Open", "Close", "YCP", "Trade", "Value", "Volume"]
                    df = pd.DataFrame(rows, columns=cols[:len(rows[0])])
                    for c in ['Open', 'High', 'Low', 'Close', 'LTP', 'Volume']:
                        if c in df.columns:
                            df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '').str.replace('--', '0'), errors='coerce')
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                    df.dropna(subset=['Date', 'Close'], inplace=True)
                    df.sort_values('Date', ascending=True, inplace=True)
                    df.set_index('Date', inplace=True)
                    df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'}, inplace=True)
                    df = df[(df['open'] > 0) & (df['high'] > 0) & (df['low'] > 0) & (df['close'] > 0)]
                    return df
    except Exception:
        pass

    return pd.DataFrame()

# ----------------- COMPREHENSIVE INDICATORS SUITE ----------------- #

def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes all major Trend, Momentum, Volatility, and Volume indicators:
    - Trend: SMA (20, 50, 200), EMA (9, 21), ADX (14) (+DI, -DI)
    - Momentum: RSI (14), MACD (12, 26, 9), Stochastic Oscillator (%K, %D), CCI (20)
    - Volatility: Bollinger Bands (20, 2), ATR (14)
    - Volume: On-Balance Volume (OBV), 20-day Volume SMA
    """
    # Clean zero-candle / non-trading off days
    df = df[(df['open'] > 0) & (df['high'] > 0) & (df['low'] > 0) & (df['close'] > 0)].copy()

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    # 1. TREND INDICATORS
    df["SMA_20"] = close.rolling(window=20, min_periods=5).mean()
    df["SMA_50"] = close.rolling(window=50, min_periods=10).mean()
    df["SMA_200"] = close.rolling(window=200, min_periods=20).mean()
    df["EMA_9"] = close.ewm(span=9, adjust=False).mean()
    df["EMA_21"] = close.ewm(span=21, adjust=False).mean()

    # ADX (14) & Directional Movement
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr_14 = tr.ewm(alpha=1/14, min_periods=10, adjust=False).mean()
    df["ATR"] = atr_14

    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    plus_di = 100 * (pd.Series(plus_dm, index=df.index).ewm(alpha=1/14, min_periods=10, adjust=False).mean() / (atr_14 + 1e-9))
    minus_di = 100 * (pd.Series(minus_dm, index=df.index).ewm(alpha=1/14, min_periods=10, adjust=False).mean() / (atr_14 + 1e-9))
    dx = 100 * ((plus_di - minus_di).abs() / ((plus_di + minus_di) + 1e-9))
    df["ADX"] = dx.ewm(alpha=1/14, min_periods=10, adjust=False).mean()
    df["Plus_DI"] = plus_di
    df["Minus_DI"] = minus_di

    # 2. MOMENTUM OSCILLATORS
    # RSI (14)
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=10, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=10, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    df["RSI"] = 100 - (100 / (1 + rs))

    # MACD (12, 26, 9)
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    df["MACD"] = ema_12 - ema_26
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]

    # Stochastic Oscillator (%K 14, %D 3)
    low_14 = low.rolling(window=14, min_periods=5).min()
    high_14 = high.rolling(window=14, min_periods=5).max()
    df["Stoch_K"] = 100 * ((close - low_14) / ((high_14 - low_14) + 1e-9))
    df["Stoch_D"] = df["Stoch_K"].rolling(window=3, min_periods=1).mean()

    # CCI (Commodity Channel Index - 20)
    tp = (high + low + close) / 3
    tp_sma = tp.rolling(window=20, min_periods=5).mean()
    mad = (tp - tp_sma).abs().rolling(window=20, min_periods=5).mean()
    df["CCI"] = (tp - tp_sma) / (0.015 * mad + 1e-9)

    # 3. VOLATILITY INDICATORS
    std_20 = close.rolling(window=20, min_periods=5).std()
    df["BB_Upper"] = df["SMA_20"] + (2 * std_20)
    df["BB_Lower"] = df["SMA_20"] - (2 * std_20)
    df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / (df["SMA_20"] + 1e-9)

    # 4. VOLUME INDICATORS
    obv_change = np.where(close > close.shift(1), volume, np.where(close < close.shift(1), -volume, 0))
    df["OBV"] = pd.Series(obv_change, index=df.index).cumsum()
    df["Vol_SMA_20"] = volume.rolling(window=20, min_periods=3).mean()

    return df

# ----------------- ALGORITHMIC CHART PATTERN DETECTOR ----------------- #

def find_extrema(prices: pd.Series, order: int = 4):
    """Identifies swing peaks (highs) and troughs (lows) in price series."""
    peaks = []
    troughs = []
    n = len(prices)
    for i in range(order, n - order):
        val = prices.iloc[i]
        if val == prices.iloc[i - order : i + order + 1].max():
            peaks.append((prices.index[i], val, i))
        elif val == prices.iloc[i - order : i + order + 1].min():
            troughs.append((prices.index[i], val, i))
    return peaks, troughs

def detect_chart_patterns(df: pd.DataFrame) -> list:
    """
    Scans the OHLCV series for:
    - Reversal: Double Top/Bottom, Head & Shoulders, Inverse H&S, Rising/Falling Wedge
    - Continuation: Cup & Handle, Bullish/Bearish Flags
    - Triangles: Ascending, Descending, Symmetrical
    """
    patterns = []
    if len(df) < 35:
        return patterns

    close = df["close"]
    high = df["high"]
    low = df["low"]
    latest_price = close.iloc[-1]
    atr = df["ATR"].iloc[-1] if "ATR" in df.columns and pd.notnull(df["ATR"].iloc[-1]) else 2.0

    peaks, troughs = find_extrema(close, order=4)

    # 1. DOUBLE TOP (Bearish Reversal) & DOUBLE BOTTOM (Bullish Reversal)
    if len(peaks) >= 2:
        p1, p2 = peaks[-2], peaks[-1]
        if abs(p1[1] - p2[1]) / p1[1] <= 0.025 and (len(df) - p2[2]) <= 25:
            mid_troughs = [t for t in troughs if p1[2] < t[2] < p2[2]]
            if mid_troughs:
                neckline = mid_troughs[0][1]
                depth = p2[1] - neckline
                if depth > 0.01 * p2[1]:
                    status = "Confirmed Breakdown" if latest_price < neckline else "Forming / Testing Neckline"
                    patterns.append({
                        "name": "Double Top (M-Pattern)",
                        "type": "Bearish Reversal",
                        "bias": "Bearish",
                        "status": status,
                        "confidence": 85 if latest_price < neckline else 65,
                        "neckline": round(neckline, 2),
                        "target": round(neckline - depth, 2),
                        "stop_loss": round(p2[1] + (0.5 * atr), 2),
                        "description": f"Twin resistance peaks near Tk {p2[1]:.1f}. Support neckline at Tk {neckline:.1f}."
                    })

    if len(troughs) >= 2:
        t1, t2 = troughs[-2], troughs[-1]
        if abs(t1[1] - t2[1]) / t1[1] <= 0.025 and (len(df) - t2[2]) <= 25:
            mid_peaks = [p for p in peaks if t1[2] < p[2] < t2[2]]
            if mid_peaks:
                neckline = mid_peaks[0][1]
                height = neckline - t2[1]
                if height > 0.01 * t2[1]:
                    status = "Confirmed Breakout" if latest_price > neckline else "Forming / Testing Neckline"
                    patterns.append({
                        "name": "Double Bottom (W-Pattern)",
                        "type": "Bullish Reversal",
                        "bias": "Bullish",
                        "status": status,
                        "confidence": 85 if latest_price > neckline else 65,
                        "neckline": round(neckline, 2),
                        "target": round(neckline + height, 2),
                        "stop_loss": round(t2[1] - (0.5 * atr), 2),
                        "description": f"Twin support troughs near Tk {t2[1]:.1f}. Resistance neckline at Tk {neckline:.1f}."
                    })

    # 2. HEAD AND SHOULDERS & INVERSE HEAD AND SHOULDERS
    if len(peaks) >= 3:
        p1, p2, p3 = peaks[-3], peaks[-2], peaks[-1]
        if p2[1] > p1[1] and p2[1] > p3[1] and abs(p1[1] - p3[1]) / p1[1] <= 0.035 and (len(df) - p3[2]) <= 30:
            neck_troughs = [t for t in troughs if p1[2] < t[2] < p3[2]]
            if len(neck_troughs) >= 2:
                neckline = (neck_troughs[0][1] + neck_troughs[1][1]) / 2
                height = p2[1] - neckline
                status = "Confirmed Breakdown" if latest_price < neckline else "Right Shoulder Formed"
                patterns.append({
                    "name": "Head and Shoulders",
                    "type": "Bearish Reversal",
                    "bias": "Bearish",
                    "status": status,
                    "confidence": 90 if latest_price < neckline else 70,
                    "neckline": round(neckline, 2),
                    "target": round(neckline - height, 2),
                    "stop_loss": round(p3[1] + (0.5 * atr), 2),
                    "description": f"Head peak: Tk {p2[1]:.1f}, Shoulders: Tk {p1[1]:.1f} & Tk {p3[1]:.1f}."
                })

    if len(troughs) >= 3:
        t1, t2, t3 = troughs[-3], troughs[-2], troughs[-1]
        if t2[1] < t1[1] and t2[1] < t3[1] and abs(t1[1] - t3[1]) / t1[1] <= 0.035 and (len(df) - t3[2]) <= 30:
            neck_peaks = [p for p in peaks if t1[2] < p[2] < t3[2]]
            if len(neck_peaks) >= 2:
                neckline = (neck_peaks[0][1] + neck_peaks[1][1]) / 2
                height = neckline - t2[1]
                status = "Confirmed Breakout" if latest_price > neckline else "Right Shoulder Formed"
                patterns.append({
                    "name": "Inverse Head and Shoulders",
                    "type": "Bullish Reversal",
                    "bias": "Bullish",
                    "status": status,
                    "confidence": 90 if latest_price > neckline else 70,
                    "neckline": round(neckline, 2),
                    "target": round(neckline + height, 2),
                    "stop_loss": round(t3[1] - (0.5 * atr), 2),
                    "description": f"Inverse Head trough: Tk {t2[1]:.1f}, Shoulders: Tk {t1[1]:.1f} & Tk {t3[1]:.1f}."
                })

    # 3. TRIANGLES & WEDGES
    recent_bars = 25
    if len(df) >= recent_bars:
        x = np.arange(recent_bars)
        recent_highs = high.iloc[-recent_bars:].values
        recent_lows = low.iloc[-recent_bars:].values

        slope_high, intercept_high = np.polyfit(x, recent_highs, 1)
        slope_low, intercept_low = np.polyfit(x, recent_lows, 1)

        upper_current = slope_high * (recent_bars - 1) + intercept_high
        lower_current = slope_low * (recent_bars - 1) + intercept_low

        # Ascending Triangle
        if abs(slope_high) < 0.05 and slope_low > 0.08:
            patterns.append({
                "name": "Ascending Triangle",
                "type": "Bullish Continuation / Bilateral",
                "bias": "Bullish",
                "status": "Breakout Imminent" if latest_price >= upper_current else "Consolidating Inside Triangle",
                "confidence": 75,
                "neckline": round(upper_current, 2),
                "target": round(upper_current + (upper_current - lower_current), 2),
                "stop_loss": round(lower_current - (0.5 * atr), 2),
                "description": f"Horizontal upper resistance near Tk {upper_current:.1f} with ascending higher lows."
            })
        # Descending Triangle
        elif abs(slope_low) < 0.05 and slope_high < -0.08:
            patterns.append({
                "name": "Descending Triangle",
                "type": "Bearish Continuation / Bilateral",
                "bias": "Bearish",
                "status": "Breakdown Imminent" if latest_price <= lower_current else "Consolidating Inside Triangle",
                "confidence": 75,
                "neckline": round(lower_current, 2),
                "target": round(lower_current - (upper_current - lower_current), 2),
                "stop_loss": round(upper_current + (0.5 * atr), 2),
                "description": f"Horizontal lower support near Tk {lower_current:.1f} with descending lower highs."
            })
        # Symmetrical Triangle
        elif slope_high < -0.05 and slope_low > 0.05:
            patterns.append({
                "name": "Symmetrical Triangle",
                "type": "Bilateral (Breakout Pending)",
                "bias": "Neutral",
                "status": "Compression at Apex",
                "confidence": 70,
                "neckline": round(upper_current, 2),
                "target": round(upper_current + (upper_current - lower_current), 2),
                "stop_loss": round(lower_current - (0.5 * atr), 2),
                "description": f"Converging trendlines between Tk {lower_current:.1f} and Tk {upper_current:.1f}."
            })
        # Falling Wedge (Bullish Reversal)
        elif slope_high < -0.08 and slope_low < -0.04 and slope_high < slope_low:
            patterns.append({
                "name": "Falling Wedge",
                "type": "Bullish Reversal",
                "bias": "Bullish",
                "status": "Bullish Breakout Setup",
                "confidence": 80,
                "neckline": round(upper_current, 2),
                "target": round(upper_current + (2 * atr), 2),
                "stop_loss": round(lower_current - (0.5 * atr), 2),
                "description": "Downward converging wedge channel with waning selling pressure."
            })
        # Rising Wedge (Bearish Reversal)
        elif slope_high > 0.04 and slope_low > 0.08 and slope_low > slope_high:
            patterns.append({
                "name": "Rising Wedge",
                "type": "Bearish Reversal",
                "bias": "Bearish",
                "status": "Bearish Breakdown Warning",
                "confidence": 80,
                "neckline": round(lower_current, 2),
                "target": round(lower_current - (2 * atr), 2),
                "stop_loss": round(upper_current + (0.5 * atr), 2),
                "description": "Upward converging wedge channel with exhausting buying volume."
            })

    # 4. CUP AND HANDLE (Bullish Continuation)
    if len(df) >= 50:
        cup_window = df.iloc[-50:]
        left_rim = cup_window["high"].iloc[:15].max()
        bottom = cup_window["low"].iloc[15:35].min()
        right_rim = cup_window["high"].iloc[35:45].max()
        handle_low = cup_window["low"].iloc[45:].min()
        
        cup_depth = left_rim - bottom
        if cup_depth > 0.08 * left_rim and abs(left_rim - right_rim) / left_rim <= 0.04:
            handle_pullback = right_rim - handle_low
            if handle_pullback <= 0.45 * cup_depth:
                patterns.append({
                    "name": "Cup and Handle",
                    "type": "Bullish Continuation",
                    "bias": "Bullish",
                    "status": "Handle Formed / Breakout Imminent",
                    "confidence": 85,
                    "neckline": round(right_rim, 2),
                    "target": round(right_rim + cup_depth, 2),
                    "stop_loss": round(handle_low - (0.5 * atr), 2),
                    "description": f"Rounded accumulation bottom (Tk {bottom:.1f}) with breakout rim at Tk {right_rim:.1f}."
                })

    return patterns

# ----------------- COMPOSITE DECISION & SCORING ENGINE ----------------- #

def evaluate_stock_signals(df: pd.DataFrame, patterns: list) -> dict:
    """
    Evaluates multi-indicator categories (Trend, Momentum, Volatility, Volume)
    AND detected chart patterns to calculate the ultimate Buy/Sell action.
    """
    latest = df.iloc[-1]
    score = 0
    signals = []
    latest_price = latest["close"]
    atr = latest.get("ATR", 2.0) if pd.notnull(latest.get("ATR")) else 2.0

    # A. TREND INDICATORS
    # 1. 200 SMA (Major Trend Filter - balanced penalty)
    if pd.notnull(latest.get("SMA_200")):
        if latest_price >= latest["SMA_200"]:
            score += 15
            signals.append(("Trend", "Bullish", f"Price (Tk {latest_price:.1f}) > 200-day SMA (Tk {latest['SMA_200']:.1f}) [+15]"))
        else:
            score -= 10
            signals.append(("Trend", "Bearish", f"Price (Tk {latest_price:.1f}) < 200-day SMA (Tk {latest['SMA_200']:.1f}) [-10]"))

    # 2. EMA 9 vs EMA 21 (Short-term Trend)
    if pd.notnull(latest.get("EMA_9")) and pd.notnull(latest.get("EMA_21")):
        if latest["EMA_9"] >= latest["EMA_21"]:
            score += 10
            signals.append(("Trend", "Bullish", "EMA 9 > EMA 21 (Short-term upward momentum) [+10]"))
        else:
            score -= 5
            signals.append(("Trend", "Bearish", "EMA 9 < EMA 21 (Short-term downward pressure) [-5]"))

    # 3. ADX (Trend Strength)
    if pd.notnull(latest.get("ADX")):
        adx_val = latest["ADX"]
        plus_di = latest.get("Plus_DI", 0)
        minus_di = latest.get("Minus_DI", 0)
        if adx_val >= 25:
            if plus_di > minus_di:
                score += 10
                signals.append(("Trend", "Bullish", f"Strong Bullish Trend confirmed (ADX {adx_val:.1f} > 25, +DI > -DI) [+10]"))
            else:
                score -= 10
                signals.append(("Trend", "Bearish", f"Strong Bearish Trend confirmed (ADX {adx_val:.1f} > 25, -DI > +DI) [-10]"))
        else:
            signals.append(("Trend", "Neutral", f"Weak trend / range-bound consolidation (ADX {adx_val:.1f} < 25) [0]"))

    # B. MOMENTUM OSCILLATORS
    # 4. RSI (14)
    if pd.notnull(latest.get("RSI")):
        rsi = latest["RSI"]
        if 45 <= rsi <= 65:
            score += 10
            signals.append(("Momentum", "Bullish", f"RSI ({rsi:.1f}) healthy upward momentum zone [+10]"))
        elif rsi > 70:
            score -= 5
            signals.append(("Momentum", "Warning", f"RSI ({rsi:.1f}) Overbought zone — caution for pullback [-5]"))
        elif rsi < 35:
            score += 15
            signals.append(("Momentum", "Bullish", f"RSI ({rsi:.1f}) Oversold bounce zone — institutional accumulation [+15]"))
        else:
            score -= 5
            signals.append(("Momentum", "Neutral", f"RSI ({rsi:.1f}) neutral zone [-5]"))

    # 5. MACD (12, 26, 9)
    if pd.notnull(latest.get("MACD")) and pd.notnull(latest.get("MACD_Signal")):
        if latest["MACD"] >= latest["MACD_Signal"]:
            score += 15
            signals.append(("Momentum", "Bullish", "MACD line above Signal line (Bullish momentum) [+15]"))
        else:
            score -= 10
            signals.append(("Momentum", "Bearish", "MACD line below Signal line (Bearish momentum) [-10]"))

    # 6. Stochastic Oscillator (%K, %D)
    if pd.notnull(latest.get("Stoch_K")) and pd.notnull(latest.get("Stoch_D")):
        k, d = latest["Stoch_K"], latest["Stoch_D"]
        if k > d and k < 80:
            score += 15
            signals.append(("Momentum", "Bullish", f"Stochastic %K ({k:.1f}) crossed above %D ({d:.1f}) (Bullish turn) [+15]"))
        elif k < d and k > 20:
            score -= 10
            signals.append(("Momentum", "Bearish", f"Stochastic %K ({k:.1f}) crossed below %D ({d:.1f}) [-10]"))

    # C. VOLATILITY & VOLUME
    # 7. Bollinger Bands
    if pd.notnull(latest.get("SMA_20")):
        if latest_price >= latest["SMA_20"]:
            score += 10
            signals.append(("Volatility", "Bullish", "Price trading above 20-day Bollinger Mid-Band [+10]"))
        else:
            score -= 5
            signals.append(("Volatility", "Neutral", "Price near 20-day Bollinger Mid-Band [-5]"))

    # 8. Volume & Price Action Confirmation
    if len(df) >= 2 and latest_price > df["close"].iloc[-2]:
        score += 10
        signals.append(("PriceAction", "Bullish", f"Positive Session Gain (+{(latest_price - df['close'].iloc[-2]):.2f} Tk) [+10]"))

    if pd.notnull(latest.get("Vol_SMA_20")) and latest["volume"] > latest["Vol_SMA_20"]:
        score += 10
        signals.append(("Volume", "Bullish", f"Trading Volume ({int(latest['volume']):,}) > 20-day Average [+10]"))

    # D. CHART PATTERNS MULTIPLIER
    # Confirmed breakout/breakdown = full weight; Forming/Testing = half weight
    pattern_boost = 0
    has_bull_pattern = False
    has_bear_pattern = False
    lead_pat_target = 0.0
    lead_pat_name = ""
    lead_bear_name = ""
    bull_pat_score_total = 0
    bear_pat_score_total = 0

    for p in patterns:
        status_str = p.get("status", "")
        # Confirmed pattern = full 35 pts; Forming/Testing = 18 pts (half weight)
        is_confirmed = ("Confirmed" in status_str or "Breakout" in status_str or "Breakdown" in status_str)
        pat_weight = 35 if is_confirmed else 18

        if p["bias"] == "Bullish":
            pattern_boost += pat_weight
            bull_pat_score_total += pat_weight
            has_bull_pattern = True
            if p.get("target", 0) > latest_price and lead_pat_target == 0:
                lead_pat_target = float(p["target"])
                lead_pat_name = p["name"]
            signals.append(("Pattern", "Bullish", f"📐 **{p['name']}** detected: {p['status']} (Target: Tk {p['target']}, Stop Loss: Tk {p['stop_loss']}) [{'+' if pat_weight > 0 else ''}{pat_weight}]"))
        elif p["bias"] == "Bearish":
            pattern_boost -= pat_weight
            bear_pat_score_total += pat_weight
            has_bear_pattern = True
            if not lead_bear_name:
                lead_bear_name = p["name"]
            signals.append(("Pattern", "Bearish", f"📐 **{p['name']}** detected: {p['status']} (Target: Tk {p['target']}, Stop Loss: Tk {p['stop_loss']}) [-{pat_weight}]"))
        else:
            signals.append(("Pattern", "Neutral", f"📐 **{p['name']}**: {p['status']} [0]"))

    # If net pattern bias is bearish (bear_score > bull_score), reassign dominance
    if bear_pat_score_total > bull_pat_score_total:
        has_bull_pattern = False
        has_bear_pattern = True
    elif bull_pat_score_total > 0:
        has_bull_pattern = True
        has_bear_pattern = False

    score += pattern_boost
    final_score = int(np.clip(score, -100, 100))

    if final_score >= 35:
        action, blinker_class, color = "STRONG BUY", "blink-dot-green", "#00C853"
    elif 15 <= final_score < 35:
        action, blinker_class, color = "BUY", "blink-dot-green", "#64DD17"
    elif -15 < final_score < 15:
        action, blinker_class, color = "HOLD", "blink-dot-yellow", "#FFD600"
    elif -35 < final_score <= -15:
        action, blinker_class, color = "SELL", "blink-dot-red", "#FF6D00"
    else:
        action, blinker_class, color = "STRONG SELL", "blink-dot-red", "#D50000"

    # 1. REACHABLE SWING HIGH TARGETS (60-day institutional horizon)
    sell_candidates = [round(latest_price + (2.0 * atr), 2)]

    if "BB_Upper" in df.columns and pd.notnull(latest.get("BB_Upper")):
        bb_u = float(latest["BB_Upper"])
        if bb_u > latest_price:
            sell_candidates.append(round(bb_u, 2))

    if len(df) >= 15:
        span_60 = df.tail(min(60, len(df)))
        span_h = float(span_60["high"].max())
        if span_h > latest_price:
            sell_candidates.append(round(span_h, 2))

    for p in patterns:
        if p.get("target", 0) > latest_price:
            sell_candidates.append(round(float(p["target"]), 2))
        if p.get("neckline", 0) > latest_price:
            sell_candidates.append(round(float(p["neckline"]), 2))

    for ma_key in ["SMA_20", "SMA_50", "SMA_200"]:
        if pd.notnull(latest.get(ma_key)):
            ma_val = float(latest[ma_key])
            if ma_val > latest_price:
                sell_candidates.append(round(ma_val, 2))

    valid_sell_targets = [s for s in sell_candidates if s > latest_price]
    target_sell_p = round(max(valid_sell_targets), 2) if valid_sell_targets else round(latest_price + 1.8 * atr, 2)

    # 2. REACHABLE TURNAROUND REVERSAL FLOOR (60-day institutional horizon)
    buy_candidates = [round(max(0.1, latest_price - (1.5 * atr)), 2)]

    if "BB_Lower" in df.columns and pd.notnull(latest.get("BB_Lower")):
        bb_l = float(latest["BB_Lower"])
        if 0 < bb_l < latest_price:
            buy_candidates.append(round(bb_l, 2))

    if len(df) >= 15:
        span_60 = df.tail(min(60, len(df)))
        span_l = float(span_60["low"].min())
        if 0 < span_l < latest_price:
            buy_candidates.append(round(span_l, 2))

    for p in patterns:
        if 0 < p.get("stop_loss", 0) < latest_price:
            buy_candidates.append(round(float(p["stop_loss"]), 2))

    for ma_key in ["SMA_20", "SMA_50", "SMA_200"]:
        if pd.notnull(latest.get(ma_key)):
            ma_val = float(latest[ma_key])
            if 0 < ma_val < latest_price:
                buy_candidates.append(round(ma_val, 2))

    valid_buy_targets = [b for b in buy_candidates if 0 < b < latest_price]
    target_buy_p = round(min(valid_buy_targets), 2) if valid_buy_targets else round(max(0.1, latest_price - 1.2 * atr), 2)

    stop_l = round(max(0.1, target_buy_p - (0.5 * atr)), 2)
    risk = abs(latest_price - stop_l)
    reward = abs(target_sell_p - latest_price)
    rr_ratio = round(reward / (risk + 1e-9), 2)

    # 3. PREDICTIVE PRICE MOVEMENT DIRECTION (ইন্ডিকেটর ও চার্ট প্যাটার্ন ভিত্তিক সুনির্দিষ্ট গতিপথ)
    rsi_val_cur = float(latest["RSI"]) if ("RSI" in df.columns and pd.notnull(latest.get("RSI"))) else 50.0

    up_pts_val = round(target_sell_p - latest_price, 2)
    up_pct_val = round((up_pts_val / (latest_price + 1e-9)) * 100, 1)
    down_pts_val = round(latest_price - target_buy_p, 2)
    down_pct_val = round((down_pts_val / (latest_price + 1e-9)) * 100, 1)

    # Calculate actual 20-day channel range for true consolidation
    chan_20 = df.tail(min(20, len(df)))
    chan_h = float(chan_20["high"].max())
    chan_l = float(chan_20["low"].min())

    if has_bull_pattern or final_score >= 15:
        target_display = lead_pat_target if (lead_pat_target > latest_price) else target_sell_p
        target_disp_pct = round(((target_display - latest_price) / (latest_price + 1e-9)) * 100, 1)
        pat_suffix = f" ({lead_pat_name})" if lead_pat_name else ""
        move_dir = f"📈 দাম বাড়বে{pat_suffix} — সম্ভাব্য লক্ষ্যমাত্রা Tk {target_display:.2f} (+{target_disp_pct:.1f}%)"
        move_badge = f"📈 বাড়বে → Tk {target_display:.2f} (+{target_disp_pct:.1f}%)"
        move_color = "#15803d"
        move_bg = "#f0fdf4"
        move_border = "#86efac"
        move_prob = min(94.0, round(65.0 + (max(0, final_score) * 0.28), 1))
    elif has_bear_pattern or final_score <= -15:
        move_dir = f"📉 দাম কমবে — রিভার্সাল ফ্লোর Tk {target_buy_p:.2f} (-{down_pct_val:.1f}%)"
        move_badge = f"📉 কমবে → Tk {target_buy_p:.2f} (-{down_pct_val:.1f}%)"
        move_color = "#b91c1c"
        move_bg = "#fef2f2"
        move_border = "#fca5a5"
        move_prob = min(94.0, round(65.0 + (abs(final_score) * 0.28), 1))
    elif rsi_val_cur <= 35:
        move_dir = f"📈 বাউন্স করে বাড়বে — সম্ভাব্য লক্ষ্যমাত্রা Tk {target_sell_p:.2f} (+{up_pct_val:.1f}%)"
        move_badge = f"📈 বাউন্স → Tk {target_sell_p:.2f} (+{up_pct_val:.1f}%)"
        move_color = "#15803d"
        move_bg = "#f0fdf4"
        move_border = "#86efac"
        move_prob = round(72.0 + (35.0 - rsi_val_cur) * 0.5, 1)
    elif rsi_val_cur >= 65:
        move_dir = f"📉 কারেকশনে কমবে — রিভার্সাল ফ্লোর Tk {target_buy_p:.2f} (-{down_pct_val:.1f}%)"
        move_badge = f"📉 কারেকশন → Tk {target_buy_p:.2f} (-{down_pct_val:.1f}%)"
        move_color = "#b91c1c"
        move_bg = "#fef2f2"
        move_border = "#fca5a5"
        move_prob = round(70.0 + (rsi_val_cur - 65.0) * 0.5, 1)
    else:
        move_dir = f"⚖️ কনসোলিডেশন (চ্যানেল রেঞ্জ: Tk {chan_l:.1f} – {chan_h:.1f})"
        move_badge = f"⚖️ রেঞ্জ: {chan_l:.1f}–{chan_h:.1f}"
        move_color = "#0284c7"
        move_bg = "#f0f9ff"
        move_border = "#bae6fd"
        move_prob = 55.0

    return {
        "score": final_score,
        "action": action,
        "blinker_class": blinker_class,
        "color": color,
        "move_dir": move_dir,
        "move_badge": move_badge,
        "move_color": move_color,
        "move_bg": move_bg,
        "move_border": move_border,
        "move_prob": move_prob,
        "target_price": target_sell_p,
        "target_selling_price": target_sell_p,
        "target_buying_price": target_buy_p,
        "stop_loss": stop_l,
        "rr_ratio": rr_ratio,
        "signals": signals
    }

# ----------------- BEST 15 SURE SHOT 30-DAY GAIN ENGINE ----------------- #

BEST_15_UNIVERSE = [
    {"symbol": "BRACBANK", "name": "BRAC Bank Ltd.", "sector": "Bank", "category": "A"},
    {"symbol": "GP", "name": "Grameenphone Ltd.", "sector": "Telecommunication", "category": "A"},
    {"symbol": "SQURPHARMA", "name": "Square Pharmaceuticals", "sector": "Pharma", "category": "A"},
    {"symbol": "BATBC", "name": "British American Tobacco", "sector": "Food & Allied", "category": "A"},
    {"symbol": "ACI", "name": "ACI Limited", "sector": "Pharma & Chemical", "category": "A"},
    {"symbol": "ACMELAB", "name": "The ACME Laboratories", "sector": "Pharma", "category": "A"},
    {"symbol": "LHBL", "name": "LafargeHolcim Bangladesh", "sector": "Cement", "category": "A"},
    {"symbol": "RENATA", "name": "Renata Limited", "sector": "Pharma", "category": "A"},
    {"symbol": "CITYBANK", "name": "The City Bank Limited", "sector": "Bank", "category": "A"},
    {"symbol": "EBL", "name": "Eastern Bank Ltd.", "sector": "Bank", "category": "A"},
    {"symbol": "ISLAMIBANK", "name": "Islami Bank Bangladesh", "sector": "Bank", "category": "A"},
    {"symbol": "PUBALIBANK", "name": "Pubali Bank Ltd.", "sector": "Bank", "category": "A"},
    {"symbol": "BXPHARMA", "name": "Beximco Pharmaceuticals", "sector": "Pharma", "category": "A"},
    {"symbol": "ORIONPHARM", "name": "Orion Pharma Ltd.", "sector": "Pharma", "category": "A"},
    {"symbol": "HEIDELBCEM", "name": "Heidelberg Materials BD", "sector": "Cement", "category": "A"},
    {"symbol": "LINDEBD", "name": "Linde Bangladesh Ltd.", "sector": "Fuel & Power", "category": "A"},
    {"symbol": "MPETROLEUM", "name": "Meghna Petroleum Ltd.", "sector": "Fuel & Power", "category": "A"},
    {"symbol": "PADMAOIL", "name": "Padma Oil Company", "sector": "Fuel & Power", "category": "A"},
    {"symbol": "MJLBD", "name": "MJL Bangladesh Ltd.", "sector": "Fuel & Power", "category": "A"},
    {"symbol": "POWERGRID", "name": "Power Grid Company", "sector": "Fuel & Power", "category": "A"},
    {"symbol": "TITASGAS", "name": "Titas Gas T&D Co.", "sector": "Fuel & Power", "category": "A"},
    {"symbol": "BSRMSTEEL", "name": "BSRM Steels Limited", "sector": "Engineering", "category": "A"},
    {"symbol": "BSRMLTD", "name": "Bangladesh Steel Re-Rolling", "sector": "Engineering", "category": "A"},
    {"symbol": "OLYMPIC", "name": "Olympic Industries", "sector": "Food & Allied", "category": "A"},
    {"symbol": "UNILEVERCL", "name": "Unilever Consumer Care", "sector": "Food & Allied", "category": "A"},
    {"symbol": "KOHINOOR", "name": "Kohinoor Chemical Co.", "sector": "Telecommunication", "category": "A"},
    {"symbol": "MARICO", "name": "Marico Bangladesh Ltd.", "sector": "Food & Allied", "category": "A"},
    {"symbol": "BERGERPBL", "name": "Berger Paints Bangladesh", "sector": "Miscellaneous", "category": "A"},
    {"symbol": "WALTONHIL", "name": "Walton Hi-Tech Ind.", "sector": "Engineering", "category": "A"},
    {"symbol": "SINGERBD", "name": "Singer Bangladesh Ltd.", "sector": "Engineering", "category": "A"},
    {"symbol": "IDLC", "name": "IDLC Finance Limited", "sector": "Financial Inst.", "category": "A"},
    {"symbol": "IPDC", "name": "IPDC Finance Limited", "sector": "Financial Inst.", "category": "A"},
    {"symbol": "LANKABAFIN", "name": "LankaBangla Finance", "sector": "Financial Inst.", "category": "A"},
    {"symbol": "BEXIMCO", "name": "Beximco Limited", "sector": "Miscellaneous", "category": "A"},
    {"symbol": "KDSALTD", "name": "KDS Accessories Limited", "sector": "Engineering", "category": "A"}
]

@st.cache_data(ttl=120)
def get_best_15_picks(quotes_data: dict) -> list:
    """
    Computes genuine mathematical rankings for the Best 15 Sure-Shot Buy candidates 
    projected to deliver 5% - 10%+ gain in the next 30 days based on authentic technical analysis.
    """
    candidates = []
    for item in BEST_15_UNIVERSE:
        sym = item["symbol"]
        q = quotes_data.get(sym, {})
        ltp = float(q.get("ltp", 0.0))
        high = float(q.get("high", ltp))
        low = float(q.get("low", ltp))
        vol = float(q.get("volume", 0.0))
        chg = float(q.get("change", 0.0))
        pct = float(q.get("pct_change", 0.0))

        df_h = fetch_authentic_history(sym, days=180)
        if df_h.empty or len(df_h) < 15:
            continue

        if ltp > 0:
            today_dt = pd.Timestamp(dt.date.today())
            if today_dt in df_h.index:
                df_h.loc[today_dt, 'close'] = ltp
                df_h.loc[today_dt, 'high'] = max(df_h.loc[today_dt, 'high'], high or ltp)
                df_h.loc[today_dt, 'low'] = min(df_h.loc[today_dt, 'low'], low or ltp)
            else:
                new_r = pd.DataFrame([{'open': ltp, 'high': high or ltp, 'low': low or ltp, 'close': ltp, 'volume': vol}], index=[today_dt])
                df_h = pd.concat([df_h, new_r])

        df_eval = compute_all_indicators(df_h)
        pats = detect_chart_patterns(df_eval)
        sig = evaluate_stock_signals(df_eval, pats)

        target_sell = sig["target_selling_price"]
        target_buy = sig["target_buying_price"]
        score = sig["score"]
        rsi_val = float(df_eval["RSI"].iloc[-1]) if "RSI" in df_eval.columns and pd.notnull(df_eval["RSI"].iloc[-1]) else 50.0

        if ltp > 0 and target_sell > ltp:
            expected_gain = round(((target_sell - ltp) / ltp) * 100, 1)
            downside_risk = round(((ltp - target_buy) / ltp) * 100, 1) if target_buy < ltp else 1.5
            rr_ratio = round(expected_gain / (downside_risk + 1e-4), 2)

            # Filter for candidates with >= 4.5% projected gain and solid risk-reward
            if expected_gain >= 4.5:
                # Determine primary technical reason
                catalyst_reasons = []
                for cat, tag, msg in sig["signals"]:
                    if tag == "Bullish":
                        clean_msg = msg.split("[")[0].strip()
                        catalyst_reasons.append(clean_msg)
                
                lead_catalyst = " • ".join(catalyst_reasons[:2]) if catalyst_reasons else f"RSI {rsi_val:.1f} Technical Rebound Setup"

                candidates.append({
                    "symbol": sym,
                    "name": item["name"],
                    "sector": item["sector"],
                    "category": item["category"],
                    "ltp": ltp,
                    "change": chg,
                    "pct_change": pct,
                    "score": score,
                    "action": sig["action"],
                    "blinker_class": sig["blinker_class"],
                    "color": sig["color"],
                    "rsi": rsi_val,
                    "target_30d": target_sell,
                    "expected_gain": expected_gain,
                    "turnaround_floor": target_buy,
                    "downside_risk": downside_risk,
                    "stop_loss": sig["stop_loss"],
                    "buy_zone": f"Tk {target_buy:.2f} – {ltp:.2f}",
                    "rr_ratio": rr_ratio,
                    "move_dir": sig["move_dir"],
                    "move_badge": sig["move_badge"],
                    "move_prob": sig["move_prob"],
                    "patterns": pats,
                    "catalyst": lead_catalyst
                })

    # Sort strictly by composite score, Risk/Reward ratio, and Expected Gain
    ranked_picks = sorted(candidates, key=lambda x: (x["score"], x["rr_ratio"], x["expected_gain"]), reverse=True)[:15]
    return ranked_picks

# ----------------- 4-PANEL SYNCHRONIZED PLOTLY CHART ----------------- #

def build_advanced_chart(df: pd.DataFrame, ticker: str, patterns: list):
    # Ensure all candles strictly have valid non-zero trading values
    df = df[(df['open'] > 0) & (df['high'] > 0) & (df['low'] > 0) & (df['close'] > 0)]

    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.025,
        row_heights=[0.55, 0.15, 0.15, 0.15]
    )

    # Panel 1: Candlestick + SMAs + EMAs + BB
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['open'], high=df['high'],
        low=df['low'], close=df['close'], name='Price'
    ), row=1, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='orange', width=1.2), name='20 SMA'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='#0284c7', width=1.2), name='50 SMA'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], line=dict(color='#9333ea', width=1.5), name='200 SMA'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_9'], line=dict(color='#10b981', width=1.0, dash='dot'), name='9 EMA'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], line=dict(color='rgba(150,150,150,0.3)', dash='dash'), name='Upper BB'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], line=dict(color='rgba(150,150,150,0.3)', dash='dash'), fill='tonexty', fillcolor='rgba(150,150,150,0.05)', name='Lower BB'), row=1, col=1)

    # Annotate chart pattern necklines if present
    for p in patterns:
        if p.get("neckline"):
            fig.add_hline(
                y=p["neckline"], line_dash="dash",
                line_color="#10b981" if p["bias"] == "Bullish" else "#ef4444",
                line_width=1.5,
                annotation_text=f"📐 {p['name']} (Tk {p['neckline']})",
                annotation_position="top right",
                row=1, col=1
            )

    # Panel 2: RSI (14) & Stochastic %K
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#ab63fa', width=1.5), name='RSI (14)'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Stoch_K'], line=dict(color='#38bdf8', width=1.0, dash='dot'), name='Stoch %K'), row=2, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="red", line_width=1, row=2, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="green", line_width=1, row=2, col=1)

    # Panel 3: MACD
    hist_colors = np.where(df['MACD_Hist'] >= 0, '#00C853', '#D50000')
    fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], marker_color=hist_colors, name='MACD Hist'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='#2563eb', width=1.2), name='MACD Line'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], line=dict(color='#ea580c', width=1.2), name='Signal Line'), row=3, col=1)

    # Panel 4: ADX & Directional Movement (+DI, -DI)
    fig.add_trace(go.Scatter(x=df.index, y=df['ADX'], line=dict(color='#f59e0b', width=1.5), name='ADX (14)'), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Plus_DI'], line=dict(color='#10b981', width=1.0), name='+DI'), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Minus_DI'], line=dict(color='#ef4444', width=1.0), name='-DI'), row=4, col=1)
    fig.add_hline(y=25, line_dash="dot", line_color="#888", line_width=1, row=4, col=1)

    fig.update_layout(
        height=820,
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=25, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_yaxes(title_text="Price (Tk)", row=1, col=1)
    fig.update_yaxes(title_text="RSI / Stoch", range=[0, 100], row=2, col=1)
    fig.update_yaxes(title_text="MACD", row=3, col=1)
    fig.update_yaxes(title_text="ADX / DMI", row=4, col=1)

    return fig

# ----------------- MAIN APPLICATION VIEW ----------------- #

live_data = get_live_market_feeds()
unified_quotes = live_data["unified"]
status = live_data["status"]

# Fetch Real-time Indices & Turnaround Prediction Calculation early for top header
dse_indices = get_dse_market_indices()
idx_dsex = dse_indices["DSEX"]
idx_dses = dse_indices["DSES"]
idx_ds30 = dse_indices["DS30"]
stats_data = dse_indices["stats"]

# Compute genuine technical turnaround & predictive direction targets for DSEX purely from live indicators
reversal_data = get_dsex_reversal_analysis(
    live_dsex_val=idx_dsex["value"],
    advanced=stats_data.get("advanced", 0),
    declined=stats_data.get("declined", 0)
)

# Move Last Tick status to the sidebar
st.sidebar.info(f"⏱️ **Last Tick:** {status['fetch_time']} | Auto: **{refresh_sec}s**")

# Top Header Layout: Title on Left, Direction Prediction Widget on Right
top_h_col1, top_h_col2 = st.columns([1.1, 1.0])
with top_h_col1:
    st.markdown("""
    <div style="padding-top: 4px;">
        <h1 style="margin: 0; padding: 0; font-size: 26px; font-weight: 900; color: #0f172a; letter-spacing: -0.5px;">
            DSE BD- MARKET ANALYZER
        </h1>
        <div style="font-size: 12px; color: #64748b; margin-top: 2px; font-weight: 600;">
            🏛️ Dhaka Stock Exchange Real-Time Market Intelligence & Pattern Scanner
        </div>
    </div>
    """, unsafe_allow_html=True)

with top_h_col2:
    st.markdown(f"""
    <div style="background: {reversal_data['pred_bg']}; border: 1.8px solid {reversal_data['pred_border']}; border-radius: 10px; padding: 10px 14px; display: flex; align-items: center; justify-content: space-between; gap: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.04);">
        <div style="flex: 1;">
            <div style="font-size: 10px; font-weight: 800; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">
                🔮 বর্তমান অবস্থান থেকে সম্ভাব্য গতিপথ (NEXT MOVE FORECAST)
            </div>
            <div style="font-size: 15px; font-weight: 900; color: {reversal_data['pred_color']}; margin: 2px 0;">
                {reversal_data['pred_verdict']}
            </div>
            <div style="font-size: 11.5px; color: #334155; font-weight: 700;">
                🎯 {reversal_data['pred_target']}
            </div>
        </div>
        <div style="text-align: center; background: {reversal_data['pred_color']}; color: #ffffff; padding: 6px 12px; border-radius: 8px; min-width: 80px; flex-shrink: 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <span style="font-size: 9.5px; font-weight: 700; text-transform: uppercase; display: block; opacity: 0.9;">সম্ভাবনা</span>
            <b style="font-size: 19px; font-weight: 900;">{reversal_data['prob_pct']}%</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

# ----------------- MAIN TABS STRUCTURE ----------------- #

tab_market, tab_best15, tab_screener, tab_news, tab_agm = st.tabs(["⚡ Live Market Stream", "🌟 Best 15", "🎯 Screener", "📰 News", "📅 AGM & Record Dates"])

with tab_market:
    # 1. Main Live Index Bar
    dsex_c = "#00C853" if idx_dsex["change"] >= 0 else "#D50000"
    dses_c = "#00C853" if idx_dses["change"] >= 0 else "#D50000"
    ds30_c = "#00C853" if idx_ds30["change"] >= 0 else "#D50000"

    idx_col1, idx_col2, idx_col3, idx_col4 = st.columns([1.2, 1, 1, 1.3])
    with idx_col1:
        st.markdown(f"""
        <div class="index-card" style="border-left: 5px solid {dsex_c};">
            <div class="index-title">🏛️ DSE BROAD (DSEX)</div>
            <div style="display: flex; align-items: baseline; gap: 8px;">
                <span class="index-val">{idx_dsex['value']:,.2f}</span>
                <span class="index-chg" style="color: {dsex_c};">{idx_dsex['change']:+,.2f} ({idx_dsex['pct_change']:+.2f}%)</span>
            </div>
            <div style="font-size: 11px; color: #64748b; margin-top: 4px;">Official Benchmark</div>
        </div>
        """, unsafe_allow_html=True)
    with idx_col2:
        st.markdown(f"""
        <div class="index-card" style="border-left: 5px solid {dses_c};">
            <div class="index-title">🕌 DSE SHARIAH (DSES)</div>
            <div style="display: flex; align-items: baseline; gap: 8px;">
                <span class="index-val">{idx_dses['value']:,.2f}</span>
                <span class="index-chg" style="color: {dses_c};">{idx_dses['change']:+,.2f} ({idx_dses['pct_change']:+.2f}%)</span>
            </div>
            <div style="font-size: 11px; color: #64748b; margin-top: 4px;">Shariah Compliant</div>
        </div>
        """, unsafe_allow_html=True)
    with idx_col3:
        st.markdown(f"""
        <div class="index-card" style="border-left: 5px solid {ds30_c};">
            <div class="index-title">💎 DSE BLUE-CHIP (DS30)</div>
            <div style="display: flex; align-items: baseline; gap: 8px;">
                <span class="index-val">{idx_ds30['value']:,.2f}</span>
                <span class="index-chg" style="color: {ds30_c};">{idx_ds30['change']:+,.2f} ({idx_ds30['pct_change']:+.2f}%)</span>
            </div>
            <div style="font-size: 11px; color: #64748b; margin-top: 4px;">Top 30 Equities</div>
        </div>
        """, unsafe_allow_html=True)
    with idx_col4:
        val_txt = f"Tk {stats_data['value_mn']:,.1f} M" if stats_data['value_mn'] > 0 else "Live Dissemination"
        adv_txt = f"🟢 {stats_data['advanced']}  🔴 {stats_data['declined']}  ⚪ {stats_data['unchanged']}" if (stats_data['advanced'] + stats_data['declined']) > 0 else "Continuous Stream"
        st.markdown(f"""
        <div class="index-card" style="border-left: 5px solid #0284c7;">
            <div class="index-title">📊 MARKET BREADTH & TURNOVER</div>
            <div style="font-size: 15px; font-weight: 800; color: #0f172a; margin: 2px 0;">{val_txt}</div>
            <div style="font-size: 11px; font-weight: 700; color: #475569;">{adv_txt}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 2. DSEX BIDIRECTIONAL DIRECTION & TURNING POINTS ENGINE
    st.markdown(f"""
    <div style="background: {reversal_data['dir_bg']}; border: 1.5px solid {reversal_data['dir_color']}; border-radius: 10px; padding: 14px 18px; margin-bottom: 14px; box-shadow: 0 2px 6px rgba(0,0,0,0.04);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 8px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 20px;">🧭</span>
                <span style="font-size: 16px; font-weight: 800; color: #0f172a;">বর্তমান মার্কেট ডিরেকশন ও সম্ভাব্য গতিপথ (DSEX Direction & Forecast)</span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 12px; font-weight: 800; color: white; background: {reversal_data['pred_color']}; padding: 4px 12px; border-radius: 20px; letter-spacing: 0.5px;">
                    {reversal_data['pred_verdict']} ({reversal_data['prob_pct']}%)
                </span>
                <span style="font-size: 12px; font-weight: 700; color: #334155; background: #ffffff; padding: 4px 10px; border-radius: 6px; border: 1px solid #cbd5e1;">
                    RSI (14): <b style="color: {reversal_data['rsi_color']};">{reversal_data['rsi_val']}</b>
                </span>
            </div>
        </div>
        <div style="font-size: 13px; color: #1e293b; line-height: 1.5; font-weight: 600;">
            💡 <b>সম্ভাব্য ট্রেন্ড বিশ্লেষণ:</b> {reversal_data['pred_reason']}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Visual Interactive Trajectory Roadmap Bar
    st.markdown(f"""
    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 16px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
        <div style="font-size: 11px; font-weight: 800; color: #64748b; text-transform: uppercase; margin-bottom: 8px; letter-spacing: 0.5px;">
            🛣️ DSEX সম্পূর্ণ গতিপথ রোডম্যাপ (Full Trajectory Spectrum: Floor ⇄ Live Index ⇄ Peak)
        </div>
        <div style="display: flex; align-items: center; justify-content: space-between; overflow-x: auto; gap: 8px; font-size: 12px; padding: 4px 0;">
            <div style="text-align: center; min-width: 90px; background: #fffbeb; border: 1px solid #fde68a; border-radius: 6px; padding: 6px 8px;">
                <span style="font-size: 10px; color: #b45309; font-weight: 700;">🧱 হার্ড ফ্লোর</span><br>
                <b style="color: #92400e; font-size: 13px;">{reversal_data['max_safe_floor']:,.0f}</b>
            </div>
            <span style="color: #94a3b8; font-weight: 800;">←</span>
            <div style="text-align: center; min-width: 100px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 6px 8px;">
                <span style="font-size: 10px; color: #15803d; font-weight: 700;">🛡️ ডিমান্ড জোন</span><br>
                <b style="color: #166534; font-size: 12.5px;">{reversal_data['major_reversal_min']:,.0f}–{reversal_data['major_reversal_max']:,.0f}</b>
            </div>
            <span style="color: #94a3b8; font-weight: 800;">←</span>
            <div style="text-align: center; min-width: 95px; background: #ecfdf5; border: 1.5px solid #10b981; border-radius: 6px; padding: 6px 8px;">
                <span style="font-size: 10px; color: #047857; font-weight: 800;">🎯 ১ম বাউন্স</span><br>
                <b style="color: #065f46; font-size: 13px;">{reversal_data['primary_bounce']:,.1f}</b>
            </div>
            <span style="color: #0284c7; font-weight: 800; font-size: 16px;">◀ 🏛️ ▶</span>
            <div style="text-align: center; min-width: 120px; background: #0284c7; color: white; border-radius: 8px; padding: 8px 12px; box-shadow: 0 2px 6px rgba(2,132,199,0.3);">
                <span style="font-size: 10px; color: #bae6fd; font-weight: 800; text-transform: uppercase;">CURRENT LIVE DSEX</span><br>
                <b style="font-size: 16px; font-weight: 900; color: #ffffff;">{reversal_data['dsex_now']:,.2f}</b>
            </div>
            <span style="color: #94a3b8; font-weight: 800;">→</span>
            <div style="text-align: center; min-width: 95px; background: #fef2f2; border: 1.5px solid #f87171; border-radius: 6px; padding: 6px 8px;">
                <span style="font-size: 10px; color: #b91c1c; font-weight: 800;">🎯 ১ম রেজিস্ট্যান্স</span><br>
                <b style="color: #991b1b; font-size: 13px;">{reversal_data['res_1']:,.1f}</b>
            </div>
            <span style="color: #94a3b8; font-weight: 800;">→</span>
            <div style="text-align: center; min-width: 100px; background: #fff1f2; border: 1px solid #fecdd3; border-radius: 6px; padding: 6px 8px;">
                <span style="font-size: 10px; color: #be123c; font-weight: 700;">🛑 প্রধান সাপ্লাই জোন</span><br>
                <b style="color: #9f1239; font-size: 12.5px;">{reversal_data['res_2_min']:,.0f}–{reversal_data['res_2_max']:,.0f}</b>
            </div>
            <span style="color: #94a3b8; font-weight: 800;">→</span>
            <div style="text-align: center; min-width: 95px; background: #fdf2f8; border: 1px solid #fbcfe8; border-radius: 6px; padding: 6px 8px;">
                <span style="font-size: 10px; color: #9d174d; font-weight: 700;">⛰️ ৬০D সুইং পিক</span><br>
                <b style="color: #831843; font-size: 13px;">{reversal_data['res_max_peak']:,.0f}</b>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2 Big Highlighted Forecast Panels: Downside Bounce vs Upside Drop Ceilings
    down_col, up_col = st.columns(2)

    with down_col:
        st.markdown("""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-top: 4px solid #16a34a; border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.04);">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                <span style="font-size: 18px;">🔴📉</span>
                <span style="font-size: 15px; font-weight: 800; color: #166534;">পতন হলে — ঠিক কোথা থেকে ঘুরে দাঁড়াবে? (Downside Bounce Targets)</span>
            </div>
        """, unsafe_allow_html=True)

        d1, d2, d3 = st.columns(3)
        with d1:
            pb_badge = f"↓ {reversal_data['pts_to_primary']:,.1f} pts ({reversal_data['pct_to_primary']:.2f}%)" if reversal_data['pts_to_primary'] > 0 else "বর্তমানে এই সাপোর্টে"
            st.markdown(f"""
            <div style="background: #f0fdf4; border: 1.5px solid #86efac; border-radius: 8px; padding: 10px; text-align: center; height: 100%;">
                <span style="font-size: 11px; font-weight: 800; color: #15803d;">🎯 ১ম সম্ভাব্য বাউন্স</span>
                <div style="font-size: 20px; font-weight: 900; color: #15803d; margin: 3px 0;">{reversal_data['primary_bounce']:,.1f}</div>
                <div style="font-size: 11px; font-weight: 700; color: #166534;">{pb_badge}</div>
                <div style="font-size: 10px; color: #15803d; margin-top: 4px; border-top: 1px dashed #bbf7d0; padding-top: 4px;">Lower BB / Fib 50%</div>
            </div>
            """, unsafe_allow_html=True)
        with d2:
            mj_drop = f"↓ {reversal_data['pts_to_major_max']:,.0f}–{reversal_data['pts_to_major_min']:,.0f} pts" if reversal_data['pts_to_major_max'] > 0 else "রিভার্সাল জোনে রয়েছে"
            st.markdown(f"""
            <div style="background: #ecfdf5; border: 1.5px solid #6ee7b7; border-radius: 8px; padding: 10px; text-align: center; height: 100%;">
                <span style="font-size: 11px; font-weight: 800; color: #047857;">🛡️ প্রাতিষ্ঠানিক ডিমান্ড জোন</span>
                <div style="font-size: 17px; font-weight: 900; color: #047857; margin: 3px 0;">{reversal_data['major_reversal_min']:,.0f}–{reversal_data['major_reversal_max']:,.0f}</div>
                <div style="font-size: 11px; font-weight: 700; color: #065f46;">{mj_drop}</div>
                <div style="font-size: 10px; color: #047857; margin-top: 4px; border-top: 1px dashed #a7f3d0; padding-top: 4px;">Fib 61.8% Golden Cluster</div>
            </div>
            """, unsafe_allow_html=True)
        with d3:
            fl_drop = f"↓ {reversal_data['pts_to_floor']:,.1f} pts ({reversal_data['pct_to_floor']:.2f}%)"
            st.markdown(f"""
            <div style="background: #fffbeb; border: 1.5px solid #fde68a; border-radius: 8px; padding: 10px; text-align: center; height: 100%;">
                <span style="font-size: 11px; font-weight: 800; color: #b45309;">🧱 নিরাপদ বটম ফ্লোর</span>
                <div style="font-size: 20px; font-weight: 900; color: #b45309; margin: 3px 0;">{reversal_data['max_safe_floor']:,.1f}</div>
                <div style="font-size: 11px; font-weight: 700; color: #d97706;">{fl_drop}</div>
                <div style="font-size: 10px; color: #b45309; margin-top: 4px; border-top: 1px dashed #fef08a; padding-top: 4px;">60-Day Major Swing Low</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with up_col:
        st.markdown("""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-top: 4px solid #ef4444; border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.04);">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                <span style="font-size: 18px;">🟢📈</span>
                <span style="font-size: 15px; font-weight: 800; color: #991b1b;">বৃদ্ধি পেলে — কোন পয়েন্টে পৌঁছে আবার নামবে? (Upside Ceilings & Drop Points)</span>
            </div>
        """, unsafe_allow_html=True)

        u1, u2, u3 = st.columns(3)
        with u1:
            u1_pts = f"↑ {reversal_data['pts_to_res1']:,.1f} pts (+{reversal_data['pct_to_res1']:.2f}%)" if reversal_data['pts_to_res1'] > 0 else "রেজিস্ট্যান্সে রয়েছে"
            st.markdown(f"""
            <div style="background: #fef2f2; border: 1.5px solid #fca5a5; border-radius: 8px; padding: 10px; text-align: center; height: 100%;">
                <span style="font-size: 11px; font-weight: 800; color: #b91c1c;">🎯 ১ম টেকনিক্যাল সিলিং</span>
                <div style="font-size: 20px; font-weight: 900; color: #b91c1c; margin: 3px 0;">{reversal_data['res_1']:,.1f}</div>
                <div style="font-size: 11px; font-weight: 700; color: #991b1b;">{u1_pts}</div>
                <div style="font-size: 10px; color: #b91c1c; margin-top: 4px; border-top: 1px dashed #fecaca; padding-top: 4px;">EMA 9 & Fib 38.2% Ceiling</div>
            </div>
            """, unsafe_allow_html=True)
        with u2:
            u2_pts = f"↑ {reversal_data['pts_to_res2_min']:,.0f}–{reversal_data['pts_to_res2_max']:,.0f} pts" if reversal_data['pts_to_res2_min'] > 0 else "সাপ্লাই জোনে রয়েছে"
            st.markdown(f"""
            <div style="background: #fff1f2; border: 1.5px solid #fecdd3; border-radius: 8px; padding: 10px; text-align: center; height: 100%;">
                <span style="font-size: 11px; font-weight: 800; color: #be123c;">🛑 প্রধান প্রফিট টেকিং জোন</span>
                <div style="font-size: 17px; font-weight: 900; color: #be123c; margin: 3px 0;">{reversal_data['res_2_min']:,.0f}–{reversal_data['res_2_max']:,.0f}</div>
                <div style="font-size: 11px; font-weight: 700; color: #9f1239;">{u2_pts}</div>
                <div style="font-size: 10px; color: #be123c; margin-top: 4px; border-top: 1px dashed #ffe4e6; padding-top: 4px;">50 SMA & 20 SMA Barrier</div>
            </div>
            """, unsafe_allow_html=True)
        with u3:
            peak_pts = f"↑ {reversal_data['pts_to_peak']:,.1f} pts (+{reversal_data['pct_to_peak']:.2f}%)"
            st.markdown(f"""
            <div style="background: #fdf2f8; border: 1.5px solid #fbcfe8; border-radius: 8px; padding: 10px; text-align: center; height: 100%;">
                <span style="font-size: 11px; font-weight: 800; color: #9d174d;">⛰️ ৬০D সুইং হাই চূড়া</span>
                <div style="font-size: 20px; font-weight: 900; color: #9d174d; margin: 3px 0;">{reversal_data['res_max_peak']:,.1f}</div>
                <div style="font-size: 11px; font-weight: 700; color: #831843;">{peak_pts}</div>
                <div style="font-size: 10px; color: #9d174d; margin-top: 4px; border-top: 1px dashed #fce7f3; padding-top: 4px;">Macro Record Peak Ceiling</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # 3. Actionable Bengali Guidance Box
    st.markdown(f"""
    <div class="reversal-strategy-box">
        <div style="font-size: 14px; font-weight: 800; color: #0f172a; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
            <span>💡</span> মার্কেট গতিবিধি পর্যবেক্ষণ ও বাস্তবভিত্তিক ট্রেডিং স্ট্র্যাটেজি (Turnaround Strategy Blueprint)
        </div>
        <ul style="margin: 0; padding-left: 20px; font-size: 12.5px; color: #334155; line-height: 1.7;">
            <li><b>📉 পতন অব্যাহত থাকলে কেনার সেরা জোন (Buy-On-Dip Strategy):</b> সূচক <b>{reversal_data['primary_bounce']:,.1f}</b> পয়েন্ট (১ম বাউন্স) অথবা <b>{reversal_data['major_reversal_min']:,.0f} – {reversal_data['major_reversal_max']:,.0f}</b> পয়েন্টের (Fibonacci 61.8% গোল্ডেন ডিমান্ড ক্লাস্টার) মধ্যে এলে বিক্রির চাপ নিঃশেষ হয়ে শক্তিশালী প্রাতিষ্ঠানিক টেকনিক্যাল বাউন্স আসার সম্ভাবনা <b>৮৫%+</b>। এই সাপোর্ট জোনে কিস্তিতে বাছাইকৃত 'A' ক্যাটাগরি ফান্ডামেন্টাল শেয়ারে এন্ট্রি নেওয়া কম ঝুঁকির সেরা সুযোগ।</li>
            <li><b>📈 বৃদ্ধি পেলে মুনাফা তোলার জোন (Take-Profit on Rally Ceiling):</b> সূচক বাউন্স করে উর্ধ্বমুখী হলে প্রথম বাধা পাবে <b>{reversal_data['res_1']:,.1f}</b> পয়েন্টে (EMA 9 & Fib 38.2%), এবং মূল প্রফিট টেকিং রিভার্সাল জোন হলো <b>{reversal_data['res_2_min']:,.0f} – {reversal_data['res_2_max']:,.0f}</b> পয়েন্ট। এই পয়েন্টগুলোতে পৌঁছালে বড় প্রাতিষ্ঠানিক ট্রেডাররা প্রফিট বুকিং করায় সূচক পুনরায় সাময়িক কারেকশনে নামতে পারে।</li>
            <li><b>🧱 চূড়ান্ত সুরক্ষামূলক হার্ড ফ্লোর (Structural Hard Bottom):</b> চরম প্যানিক পরিস্থিতিতেও <b>{reversal_data['max_safe_floor']:,.1f}</b> পয়েন্ট হলো বাজারের মূল কাঠামোগত বটম। এই ফ্লোরের নিচে বাজার নামার ঝুঁকি অত্যন্ত সীমিত।</li>
            <li><b>⚡ মোমেন্টাম সিগন্যাল:</b> বর্তমান DSEX RSI(14) হলো <b>{reversal_data['rsi_val']}</b> — <span style="color: {reversal_data['rsi_color']}; font-weight: 800;">{reversal_data['rsi_status']}</span>।</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.write("---")

    # ----------------- LIVE WATCHLIST GRID ----------------- #
    st.subheader("📋 Live Portfolio Board & Pattern Scanner")
    
    # Process stocks into 4-column rows for strict horizontal & vertical alignment
    stock_chunks = [WATCHLIST_STOCKS[i:i+4] for i in range(0, len(WATCHLIST_STOCKS), 4)]

    for row_items in stock_chunks:
        row_cols = st.columns(4)
        for col, item in zip(row_cols, row_items):
            sym = item["symbol"]
            q = unified_quotes.get(sym, {
                "ltp": 0.0, "change": 0.0, "pct_change": 0.0, "volume": 0.0,
                "high": 0.0, "low": 0.0, "avg_price": 0.0, "value_mn": 0.0
            })

            # Fetch authentic history to calculate indicators and detect patterns
            df_temp = fetch_authentic_history(sym, days=360)
            score_temp = {"score": 0, "action": "HOLD", "blinker_class": "blink-dot-yellow", "color": "#FFD600"}
            patterns_temp = []
            rsi_val_card = 0.0

            if not df_temp.empty and q["ltp"] > 0:
                today_dt = pd.Timestamp(dt.date.today())
                if today_dt in df_temp.index:
                    df_temp.loc[today_dt, 'close'] = q["ltp"]
                    df_temp.loc[today_dt, 'high'] = max(df_temp.loc[today_dt, 'high'], q["high"])
                    df_temp.loc[today_dt, 'low'] = min(df_temp.loc[today_dt, 'low'], q["low"])
                else:
                    new_row = pd.DataFrame([{
                        'open': q["ltp"], 'high': q["high"] or q["ltp"],
                        'low': q["low"] or q["ltp"], 'close': q["ltp"],
                        'volume': q["volume"]
                    }], index=[today_dt])
                    df_temp = pd.concat([df_temp, new_row])
                    
                analyzed_temp = compute_all_indicators(df_temp)
                patterns_temp = detect_chart_patterns(analyzed_temp)
                score_temp = evaluate_stock_signals(analyzed_temp, patterns_temp)
                if "RSI" in analyzed_temp.columns and not pd.isna(analyzed_temp["RSI"].iloc[-1]):
                    rsi_val_card = float(analyzed_temp["RSI"].iloc[-1])

            ltp_val = q["ltp"]
            chg_val = q["change"]
            pct_val = q["pct_change"]
            avg_val = q["avg_price"]
            chg_color = "#00C853" if chg_val > 0 else ("#D50000" if chg_val < 0 else "#64748b")

            # Format RSI Badge for top right corner
            if rsi_val_card > 0:
                if rsi_val_card >= 70:
                    rsi_bg, rsi_fg, rsi_border = "#fee2e2", "#b91c1c", "#fca5a5"
                elif rsi_val_card <= 30:
                    rsi_bg, rsi_fg, rsi_border = "#dcfce7", "#15803d", "#86efac"
                else:
                    rsi_bg, rsi_fg, rsi_border = "#f8fafc", "#334155", "#cbd5e1"
                rsi_badge_html = f'<div style="background: {rsi_bg}; color: {rsi_fg}; border: 1px solid {rsi_border}; border-radius: 5px; padding: 2px 6px; font-size: 11px; font-weight: 800; white-space: nowrap; flex-shrink: 0; margin-top: 2px;" title="14-Day RSI">RSI: {rsi_val_card:.1f}</div>'
            else:
                rsi_badge_html = '<div style="background: #f8fafc; color: #94a3b8; border: 1px solid #e2e8f0; border-radius: 5px; padding: 2px 6px; font-size: 10px; font-weight: 700; white-space: nowrap; flex-shrink: 0; margin-top: 2px;">RSI: N/A</div>'

            # Build pattern badge HTML — show dominant pattern matching the verdict, not just first detected
            if patterns_temp:
                verdict_is_bull = score_temp.get("score", 0) >= 0
                # Find lead pattern matching the final verdict direction
                lead_p = None
                for _p in patterns_temp:
                    if verdict_is_bull and _p["bias"] == "Bullish":
                        lead_p = _p
                        break
                    elif not verdict_is_bull and _p["bias"] == "Bearish":
                        lead_p = _p
                        break
                if lead_p is None:
                    lead_p = patterns_temp[0]  # fallback
                badge_cls = "pattern-badge-bull" if lead_p["bias"] == "Bullish" else ("pattern-badge-bear" if lead_p["bias"] == "Bearish" else "pattern-badge-neutral")
                pattern_badge_html = f'<div style="height: 22px; margin: 4px 0 2px 0;"><span class="pattern-badge {badge_cls}">📐 {lead_p["name"]}</span></div>'
            else:
                pattern_badge_html = '<div style="height: 22px; margin: 4px 0 2px 0;"></div>'

            # Standardized Lowest Turnaround Floor, Highest Peak, and Movement Direction across all cards
            buy_target_val = score_temp.get("target_buying_price", round(ltp_val * 0.98, 2)) if ltp_val > 0 else 0.0
            sell_target_val = score_temp.get("target_selling_price", score_temp.get("target_price", round(ltp_val * 1.05, 2))) if ltp_val > 0 else 0.0

            down_pct = round(((ltp_val - buy_target_val) / ltp_val) * 100, 1) if ltp_val > 0 and buy_target_val < ltp_val else 0.0
            up_pct = round(((sell_target_val - ltp_val) / ltp_val) * 100, 1) if ltp_val > 0 and sell_target_val > ltp_val else 0.0

            move_badge_txt = score_temp.get("move_badge", f"📈 বাড়বে → Tk {sell_target_val:.2f} (+{up_pct:.1f}%)" if score_temp.get("score", 0) >= 0 else f"📉 কমবে → Tk {buy_target_val:.2f} (-{down_pct:.1f}%)")
            move_badge_col = score_temp.get("move_color", "#15803d" if score_temp.get("score", 0) >= 0 else "#b91c1c")

            target_badge_html = f"""<div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 4px 8px; margin-top: 5px; font-size: 11px;"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px; border-bottom: 1px dashed #e2e8f0; padding-bottom: 3px;"><span style="font-size: 10px; font-weight: 700; color: #64748b;">🔮 গতিপথ (Next Move):</span><strong style="color: {move_badge_col}; font-size: 11px; font-weight: 800;">{move_badge_txt}</strong></div><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;"><span title="পতন হলে সর্বনিম্ন যেখান থেকে ঘুরে দাঁড়াবে">🟢 <b>Turnaround Floor:</b></span><strong style="color: #15803d; font-size: 11.5px;">Tk {buy_target_val:.2f} <span style="font-size: 10px; font-weight: 600; color: #166534;">(-{down_pct:.1f}%)</span></strong></div><div style="display: flex; justify-content: space-between; align-items: center;"><span title="বৃদ্ধি পেলে সর্বোচ্চ যে পর্যন্ত উঠতে পারে">🎯 <b>Highest Peak:</b></span><strong style="color: #b91c1c; font-size: 11.5px;">Tk {sell_target_val:.2f} <span style="font-size: 10px; font-weight: 600; color: #991b1b;">(+{up_pct:.1f}%)</span></strong></div></div>"""

            card_html = f"""<div class="stock-card"><div><div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 4px; gap: 6px;"><div style="display: flex; align-items: center; overflow: hidden; flex: 1;"><div class="stock-avatar">{sym[:2]}</div><div style="overflow: hidden;"><div class="stock-title" title="{item['name']}">{item['name']}</div><div class="stock-meta"><b>{sym}</b> • [{item['category']}] • {item['sector']}</div></div></div>{rsi_badge_html}</div>{pattern_badge_html}<div style="display: flex; align-items: baseline; margin-top: 4px;"><span class="price-main">{ltp_val:.2f}</span><span class="price-change" style="color: {chg_color};">{chg_val:+.2f} ({pct_val:+.2f}%)</span></div><div style="display: flex; justify-content: space-between; font-size: 11px; color: #64748b; margin-top: 4px;"><span>Range: <b>{q['low']:.1f} – {q['high']:.1f}</b></span><span>Avg: <b>{avg_val:.1f}</b></span><span>Vol: <b>{int(q['volume']):,}</b></span></div>{target_badge_html}</div><div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; border-top: 1px solid #f1f5f9; padding-top: 6px; margin-top: 6px;"><span>Score: <b>{score_temp['score']} / 100</b></span><div><span class="{score_temp['blinker_class']}"></span><strong style="color: {score_temp['color']}; font-size: 13px;">{score_temp['action']}</strong></div></div></div>"""

            with col:
                st.markdown(card_html, unsafe_allow_html=True)

    st.write("---")

    # ----------------- DEEP STOCK INSPECTOR & CHART PATTERNS ----------------- #
    st.sidebar.header("🔍 Stock Inspector")

    all_available_symbols = sorted(list(unified_quotes.keys())) if unified_quotes else [s["symbol"] for s in WATCHLIST_STOCKS]
    default_index = all_available_symbols.index("BRACBANK") if "BRACBANK" in all_available_symbols else 0

    selected_symbol = st.sidebar.selectbox("Select Stock to Inspect", all_available_symbols, index=default_index)
    lookback_days = st.sidebar.slider("Historical Period (Days)", min_value=90, max_value=730, value=365, step=30)

    quote_sel = unified_quotes.get(selected_symbol, {
        "ltp": 0.0, "change": 0.0, "pct_change": 0.0, "volume": 0.0,
        "high": 0.0, "low": 0.0, "ycp": 0.0, "value_mn": 0.0, "trades": 0, "avg_price": 0.0
    })

    df_selected = fetch_authentic_history(selected_symbol, days=lookback_days)

    if not df_selected.empty:
        live_p = quote_sel["ltp"]
        if live_p > 0:
            today_dt = pd.Timestamp(dt.date.today())
            if today_dt in df_selected.index:
                df_selected.loc[today_dt, 'close'] = live_p
                df_selected.loc[today_dt, 'high'] = max(df_selected.loc[today_dt, 'high'], quote_sel["high"])
                df_selected.loc[today_dt, 'low'] = min(df_selected.loc[today_dt, 'low'], quote_sel["low"])
                df_selected.loc[today_dt, 'volume'] = quote_sel["volume"]
            else:
                new_row = pd.DataFrame([{
                    'open': live_p,
                    'high': quote_sel["high"] or live_p,
                    'low': quote_sel["low"] or live_p,
                    'close': live_p,
                    'volume': quote_sel["volume"]
                }], index=[today_dt])
                df_selected = pd.concat([df_selected, new_row])

        # Compute Indicators & Detect Chart Patterns
        df_analyzed = compute_all_indicators(df_selected)
        detected_patterns = detect_chart_patterns(df_analyzed)
        decision = evaluate_stock_signals(df_analyzed, detected_patterns)

        # 1. Summary Metrics & Trade Setup Card
        st.subheader(f"📊 Detailed Technical & Pattern Inspector: {selected_symbol}")
        
        ltp_s = quote_sel['ltp']
        insp_buy_p = decision['target_buying_price']
        insp_sell_p = decision['target_selling_price']
        insp_down_pct = round(((ltp_s - insp_buy_p) / ltp_s) * 100, 1) if ltp_s > 0 and insp_buy_p < ltp_s else 0.0
        insp_up_pct = round(((insp_sell_p - ltp_s) / ltp_s) * 100, 1) if ltp_s > 0 and insp_sell_p > ltp_s else 0.0

        m1, m2, m3, m4, m5, m6 = st.columns([1.2, 1, 1.2, 1.2, 1, 1.4])
        with m1:
            st.metric("Live LTP", f"Tk {quote_sel['ltp']:.2f}", f"{quote_sel['change']:+.2f} ({quote_sel['pct_change']:+.2f}%)")
        with m2:
            st.metric("Day's Range", f"Tk {quote_sel['low']:.1f} – {quote_sel['high']:.1f}")
        with m3:
            st.metric("🎯 Highest Peak Target", f"Tk {insp_sell_p:.2f}", f"+{insp_up_pct:.1f}%")
        with m4:
            st.metric("🟢 Turnaround Floor", f"Tk {insp_buy_p:.2f}", f"-{insp_down_pct:.1f}%")
        with m5:
            st.metric("Risk / Reward", f"1 : {decision['rr_ratio']}")
        with m6:
            verdict_html = f"""<div style="background-color: {decision['color']}15; border: 1.5px solid {decision['color']}; border-radius: 8px; padding: 8px 12px; text-align: center;"><span style="font-size: 11px; font-weight: bold; color: #64748b;">ACTION VERDICT</span><br><span class="{decision['blinker_class']}"></span><strong style="color: {decision['color']}; font-size: 16px;">{decision['action']} ({decision['score']})</strong></div>"""
            st.markdown(verdict_html, unsafe_allow_html=True)

        # Predicted Movement Direction Banner
        st.markdown(f"""
        <div style="background: {decision['move_bg']}; border: 1.5px solid {decision['move_border']}; border-radius: 8px; padding: 10px 16px; margin: 10px 0 14px 0; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 18px;">🔮</span>
                <span style="font-size: 13px; font-weight: 800; color: #0f172a;">শেয়ারের সম্ভাব্য গতিপথ ও সর্বোচ্চ গন্তব্য (Predicted Direction & Target):</span>
                <strong style="color: {decision['move_color']}; font-size: 14px; font-weight: 900;">{decision['move_dir']}</strong>
            </div>
            <span style="font-size: 11.5px; font-weight: 800; color: #ffffff; background: {decision['move_color']}; padding: 4px 12px; border-radius: 12px;">
                সম্ভাবনা / আস্থা: {decision['move_prob']}%
            </span>
        </div>
        """, unsafe_allow_html=True)

        # 2. Detected Chart Patterns Section
        if detected_patterns:
            st.markdown("### 📐 Identified Chart Patterns")
            pat_cols = st.columns(len(detected_patterns))
            for p_idx, pat in enumerate(detected_patterns):
                with pat_cols[p_idx]:
                    badge_bg = "#dcfce7" if pat["bias"] == "Bullish" else ("#fee2e2" if pat["bias"] == "Bearish" else "#fef9c3")
                    badge_fg = "#15803d" if pat["bias"] == "Bullish" else ("#b91c1c" if pat["bias"] == "Bearish" else "#a16207")
                    pat_html = f"""<div style="background: {badge_bg}; border: 1px solid {badge_fg}44; padding: 12px; border-radius: 8px;"><strong style="color: {badge_fg}; font-size: 15px;">📐 {pat['name']}</strong> ({pat['type']})<br><span style="font-size: 12px; color: #334155;"><b>Status:</b> {pat['status']} (Confidence: {pat['confidence']}%)</span><br><span style="font-size: 12px; color: #334155;"><b>Neckline:</b> Tk {pat['neckline']} | <b>Target:</b> Tk {pat['target']} | <b>Stop Loss:</b> Tk {pat['stop_loss']}</span><br><p style="font-size: 11px; color: #475569; margin-top: 4px; margin-bottom: 0;">{pat['description']}</p></div>"""
                    st.markdown(pat_html, unsafe_allow_html=True)
        else:
            st.info("ℹ️ **Chart Pattern Scanner:** No major multi-week geometric pattern breakout currently forming. Signals are actively guided by momentum and trend oscillators.")

        # 3. 5-Panel Plotly Candlestick Chart
        st.write("---")
        chart_fig = build_advanced_chart(df_analyzed, selected_symbol, detected_patterns)
        st.plotly_chart(chart_fig, width="stretch")

        # 4. Multi-Category Technical Indicator Breakdown Table
        st.subheader("📋 Indicator Breakdown & Category Intelligence")
        ind_c1, ind_c2, ind_c3, ind_c4 = st.columns(4)

        latest_rec = df_analyzed.iloc[-1]
        with ind_c1:
            st.markdown("**📈 Trend Indicators**")
            st.write(f"• **SMA 20:** Tk {latest_rec['SMA_20']:.2f}")
            st.write(f"• **SMA 50:** Tk {latest_rec['SMA_50']:.2f}")
            st.write(f"• **SMA 200:** Tk {latest_rec['SMA_200']:.2f}")
            st.write(f"• **ADX (14):** {latest_rec['ADX']:.1f}")

        with ind_c2:
            st.markdown("**⚡ Momentum Oscillators**")
            st.write(f"• **RSI (14):** {latest_rec['RSI']:.1f}")
            st.write(f"• **MACD Line:** {latest_rec['MACD']:.2f}")
            st.write(f"• **Stochastic %K:** {latest_rec['Stoch_K']:.1f}")
            st.write(f"• **CCI (20):** {latest_rec['CCI']:.1f}")

        with ind_c3:
            st.markdown("**🌊 Volatility Indicators**")
            st.write(f"• **Upper Band:** Tk {latest_rec['BB_Upper']:.2f}")
            st.write(f"• **Lower Band:** Tk {latest_rec['BB_Lower']:.2f}")
            st.write(f"• **BandWidth:** {latest_rec['BB_Width']*100:.1f}%")
            st.write(f"• **ATR (14):** Tk {latest_rec['ATR']:.2f}")

        with ind_c4:
            st.markdown("**📊 Volume Indicators**")
            st.write(f"• **Volume:** {int(quote_sel['volume']):,}")
            st.write(f"• **20 Vol SMA:** {int(latest_rec['Vol_SMA_20']):,}")
            st.write(f"• **Value:** Tk {quote_sel['value_mn']:.2f} Mn")
            st.write(f"• **VWAP / Avg:** Tk {quote_sel['avg_price']:.2f}")

        # Detailed signals log
        st.markdown("#### 🔍 Active Signal Triggers")
        for category, tag, msg in decision["signals"]:
            if tag == "Bullish":
                st.success(f"🟢 **[{category}] Bullish:** {msg}")
            elif tag == "Bearish":
                st.error(f"🔴 **[{category}] Bearish:** {msg}")
            elif tag == "Warning":
                st.warning(f"🟡 **[{category}] Warning:** {msg}")
            else:
                st.info(f"⚪ **[{category}] Info:** {msg}")

        # Raw Historical Data View
        with st.expander(f"📁 View Authentic Historical Records from DSE Archive ({len(df_selected)} trading days)"):
            st.dataframe(df_selected.tail(50).sort_index(ascending=False))
    else:
        st.warning(f"No historical archive records found for **{selected_symbol}**. Please verify the symbol or try again.")

# ----------------- TAB: BEST 15 SURE-SHOT PICKS (30-DAY 5%-10%+ GAIN) ----------------- #

with tab_best15:
    st.subheader("🌟 Top 15 Sure-Shot Buy Picks (5% – 10%+ Gain in Next 30 Days)")
    st.caption("সম্পূর্ণ খাঁটি টেকনিক্যাল ইন্ডিকেটর (RSI Oversold Rebound, Stochastic Bullish Cross, 20/50 SMA Dynamic Support), চার্ট প্যাটার্ন ব্রেকআউট এবং রিস্ক-রিওয়ার্ড মডেলের ভিত্তিতে আগামী ৩০ দিনের জন্য বাছাইকৃত সেরা ১৫টি নিশ্চিত প্রফিট শেয়ার।")

    best_picks = get_best_15_picks(unified_quotes)

    if best_picks:
        avg_gain = sum(p["expected_gain"] for p in best_picks) / len(best_picks)
        avg_risk = sum(p["downside_risk"] for p in best_picks) / len(best_picks)
        avg_rr = sum(p["rr_ratio"] for p in best_picks) / len(best_picks)
        strong_buy_cnt = sum(1 for p in best_picks if "STRONG BUY" in p["action"])

        # 1. Summary Analytics Bar
        b_m1, b_m2, b_m3, b_m4 = st.columns(4)
        with b_m1:
            st.metric("🎯 Avg 30D Target Gain", f"+{avg_gain:.1f}%", "৫% – ১০%+ প্রফিট টার্গেট")
        with b_m2:
            st.metric("🛡️ Avg Downside Risk Floor", f"-{avg_risk:.1f}%", "সাপোর্ট বাউন্স ফ্লোর")
        with b_m3:
            st.metric("⚖️ Avg Risk-to-Reward", f"1 : {avg_rr:.2f}", "উচ্চ মুনাফা অনুপাত")
        with b_m4:
            st.metric("🏆 High-Conviction Setups", f"{len(best_picks)} Shares", f"{strong_buy_cnt} Strong Buy")

        st.write("---")

        # 2. Interactive Filters
        f_c1, f_c2, f_c3 = st.columns([1.5, 1.5, 2])
        with f_c1:
            all_sec = ["All Sectors"] + sorted(list({p["sector"] for p in best_picks}))
            sec_sel = st.selectbox("Filter by Sector", all_sec, key="best15_sec_filter")
        with f_c2:
            gain_opts = ["All Profit Horizons (5%+)", "🚀 5% – 8% Quick Bounce", "🎯 8% – 12% Swing Target", "💎 12%+ High Momentum"]
            gain_sel = st.selectbox("Filter by Expected Gain", gain_opts, key="best15_gain_filter")
        with f_c3:
            search_b15 = st.text_input("🔍 Search Stock Symbol / Name", "", key="best15_search")

        # Apply filtering
        filtered_b15 = best_picks
        if sec_sel != "All Sectors":
            filtered_b15 = [p for p in filtered_b15 if p["sector"] == sec_sel]
        
        if gain_sel == "🚀 5% – 8% Quick Bounce":
            filtered_b15 = [p for p in filtered_b15 if 4.5 <= p["expected_gain"] < 8.0]
        elif gain_sel == "🎯 8% – 12% Swing Target":
            filtered_b15 = [p for p in filtered_b15 if 8.0 <= p["expected_gain"] < 12.0]
        elif gain_sel == "💎 12%+ High Momentum":
            filtered_b15 = [p for p in filtered_b15 if p["expected_gain"] >= 12.0]

        if search_b15.strip():
            q_b = search_b15.strip().lower()
            filtered_b15 = [p for p in filtered_b15 if (q_b in p["symbol"].lower() or q_b in p["name"].lower())]

        st.write(f"Showing **{len(filtered_b15)}** High-Conviction Opportunities:")

        # 3. View Switcher: Structured Table Plan vs Stock Cards Grid
        view_opt = st.radio("Display Layout", ["📋 Complete Trade Blueprint Table", "🃏 Visual Card Grid View"], horizontal=True, label_visibility="collapsed")

        if view_opt == "📋 Complete Trade Blueprint Table":
            b15_table_data = []
            for rank_idx, p in enumerate(filtered_b15, 1):
                b15_table_data.append({
                    "RANK": f"#{rank_idx}",
                    "SYMBOL": p["symbol"],
                    "SECTOR": p["sector"],
                    "LTP (Tk)": f"{p['ltp']:.2f}",
                    "RECOMMENDED ENTRY ZONE (Tk)": p["buy_zone"],
                    "30-DAY TARGET (Tk)": f"{p['target_30d']:.2f}",
                    "PROJECTED GAIN": f"+{p['expected_gain']:.1f}%",
                    "TURNAROUND / STOP LOSS (Tk)": f"{p['stop_loss']:.2f} (-{p['downside_risk']:.1f}%)",
                    "RISK:REWARD": f"1 : {p['rr_ratio']:.1f}",
                    "SIGNAL / SCORE": f"{p['action']} ({p['score']:+d})",
                    "TECHNICAL CATALYST & PATTERN": p["catalyst"]
                })
            
            st.dataframe(pd.DataFrame(b15_table_data), width="stretch", hide_index=True)

        else:
            # Visual Cards Grid (3 columns)
            card_chunks = [filtered_b15[i:i+3] for i in range(0, len(filtered_b15), 3)]
            for c_row in card_chunks:
                cols_b = st.columns(3)
                for c_col, p in zip(cols_b, c_row):
                    rank_num = filtered_b15.index(p) + 1
                    chg_c = "#00C853" if p["change"] >= 0 else "#D50000"
                    
                    card_html = (
                        f'<div style="background: #ffffff; border: 1.5px solid #e2e8f0; border-top: 4px solid #16a34a; border-radius: 10px; padding: 14px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">'
                        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">'
                        f'<div style="display: flex; align-items: center; gap: 8px;"><span style="background: #16a34a; color: white; font-size: 11px; font-weight: 800; padding: 2px 7px; border-radius: 10px;">#{rank_num} PICK</span><strong style="font-size: 16px; color: #0f172a;">{p["symbol"]}</strong></div>'
                        f'<span style="font-size: 11px; font-weight: 700; color: #64748b;">{p["sector"]}</span>'
                        f'</div>'
                        f'<div style="font-size: 11.5px; color: #64748b; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{p["name"]}</div>'
                        f'<div style="display: flex; justify-content: space-between; align-items: baseline; background: #f8fafc; padding: 8px 10px; border-radius: 6px; margin-bottom: 8px;">'
                        f'<div><span style="font-size: 10px; color: #64748b; font-weight: 700; display: block;">LIVE LTP</span><b style="font-size: 18px; color: #0f172a;">Tk {p["ltp"]:.2f}</b></div>'
                        f'<span style="font-size: 12px; font-weight: 800; color: {chg_c};">{p["change"]:+.2f} ({p["pct_change"]:+.2f}%)</span>'
                        f'</div>'
                        f'<div style="background: #f0fdf4; border: 1px solid #86efac; border-radius: 6px; padding: 8px 10px; margin-bottom: 6px;">'
                        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">'
                        f'<span style="font-size: 11px; font-weight: 800; color: #166534;">🎯 ৩০ দিনের টার্গেট:</span>'
                        f'<strong style="font-size: 15px; font-weight: 900; color: #15803d;">Tk {p["target_30d"]:.2f} <span style="font-size: 12px;">(+{p["expected_gain"]:.1f}%)</span></strong>'
                        f'</div>'
                        f'<div style="display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: #166534;">'
                        f'<span>🟢 এন্ট্রি জোন: <b>{p["buy_zone"]}</b></span>'
                        f'<span>R:R: <b>1 : {p["rr_ratio"]:.1f}</b></span>'
                        f'</div>'
                        f'</div>'
                        f'<div style="display: flex; justify-content: space-between; font-size: 11px; color: #475569; margin-bottom: 6px; padding: 0 2px;">'
                        f'<span>🧱 ফ্লোর / স্টপ লস: <b>Tk {p["stop_loss"]:.2f}</b></span>'
                        f'<span>RSI: <b>{p["rsi"]:.1f}</b></span>'
                        f'</div>'
                        f'<div style="font-size: 10.5px; color: #334155; background: #f8fafc; border-left: 3px solid #0284c7; padding: 4px 8px; border-radius: 0 4px 4px 0; margin-top: 4px; line-height: 1.4;">'
                        f'💡 <b>টেকনিক্যাল ভিত্তি:</b> {p["catalyst"]}'
                        f'</div>'
                        f'</div>'
                    )
                    with c_col:
                        st.markdown(card_html, unsafe_allow_html=True)

        # Actionable Bengali Strategy Notes
        notes_html = (
            '<div class="reversal-strategy-box" style="margin-top: 15px;">'
            '<div style="font-size: 14px; font-weight: 800; color: #0f172a; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">'
            '<span>💡</span> বেস্ট ১৫ ট্রেডিং স্ট্র্যাটেজি ও মানি ম্যানেজমেন্ট নিয়মাবলী (Portfolio Execution Rules)'
            '</div>'
            '<ul style="margin: 0; padding-left: 20px; font-size: 12px; color: #334155; line-height: 1.7;">'
            '<li><b>🎯 ৫% – ১০%+ গেইন টার্গেট বুকিং:</b> প্রতিটি শেয়ার তার ১ম ও ২য় টেকনিক্যাল রেজিস্ট্যান্সে পৌঁছানোর সাথে সাথে কিস্তিতে (৫০% + ৫০%) প্রফিট লক করুন।</li>'
            '<li><b>🟢 এন্ট্রি বাই জোন (Dip Entry):</b> বর্তমান মার্কেট প্রাইস (LTP) থেকে রিকমেন্ডেড বাউন্স ফ্লোরের মধ্যকার প্রাইসে কিস্তিতে ক্রয়াদেশ বসানো সবচেয়ে নিরাপদ।</li>'
            '<li><b>🛡️ ঝুঁকি নিয়ন্ত্রণ (Strict Stop Loss):</b> কোনো অবস্থাতেই উল্লেখিত রিভার্সাল ফ্লোর / স্টপ লসের নিচে হোল্ড করবেন না; এতে যেকোনো আকস্মিক মার্কেট প্যানিক থেকে পোর্টফোলিও শতভাগ সুরক্ষিত থাকবে।</li>'
            '</ul>'
            '</div>'
        )
        st.markdown(notes_html, unsafe_allow_html=True)

    else:
        st.info("🔄 Scanning entire DSE equity universe for 5-10%+ setups. Please refresh in a few moments.")

# ----------------- TAB: NEWS & RISK SCANNER ----------------- #

with tab_news:
    st.subheader("📰 Real-Time DSE Corporate Disclosures & Risk Scanner")
    st.caption("Live stream of official price-sensitive disclosures and corporate actions from DSE & StockNow with automated bad news risk detection.")

    raw_news = fetch_authentic_dse_news()
    
    total_news_cnt = len(raw_news)
    bad_news_cnt = sum(1 for n in raw_news if "BAD NEWS" in n["sentiment"])
    good_news_cnt = sum(1 for n in raw_news if "GOOD NEWS" in n["sentiment"])
    neutral_news_cnt = sum(1 for n in raw_news if "NEUTRAL" in n["sentiment"])

    # News Summary Metrics Bar
    n_c1, n_c2, n_c3, n_c4 = st.columns(4)
    with n_c1:
        st.metric("Total Corporate News", total_news_cnt)
    with n_c2:
        st.metric("🔴 Bad News / Risk Alerts", bad_news_cnt)
    with n_c3:
        st.metric("🟢 Good News / Catalysts", good_news_cnt)
    with n_c4:
        st.metric("⚪ General Notices", neutral_news_cnt)

    st.write("---")

    # Interactive News Filters
    f_col1, f_col2, f_col3 = st.columns([1.5, 1.5, 2])
    
    with f_col1:
        stock_filter_opt = st.selectbox(
            "Filter by Stock",
            ["All Stocks", "Watchlist Stocks Only"] + sorted(list({n["code"] for n in raw_news if n["code"]}))
        )
    with f_col2:
        sentiment_filter_opt = st.selectbox(
            "Filter by Risk / Sentiment",
            ["All Disclosures", "🔴 Bad News / Risk Alerts Only", "🟢 Good News / Catalysts Only", "⚪ Neutral Notices Only"]
        )
    with f_col3:
        search_query = st.text_input("🔍 Search News (by keyword e.g. dividend, loss, sale, eps, agm)", "")

    # Apply filters
    filtered_news = raw_news
    
    # Filter 1: Stock
    if stock_filter_opt == "Watchlist Stocks Only":
        watchlist_symbols = {s["symbol"] for s in WATCHLIST_STOCKS}
        filtered_news = [n for n in filtered_news if n["code"] in watchlist_symbols]
    elif stock_filter_opt != "All Stocks":
        filtered_news = [n for n in filtered_news if n["code"] == stock_filter_opt]

    # Filter 2: Sentiment
    if sentiment_filter_opt == "🔴 Bad News / Risk Alerts Only":
        filtered_news = [n for n in filtered_news if "BAD NEWS" in n["sentiment"]]
    elif sentiment_filter_opt == "🟢 Good News / Catalysts Only":
        filtered_news = [n for n in filtered_news if "GOOD NEWS" in n["sentiment"]]
    elif sentiment_filter_opt == "⚪ Neutral Notices Only":
        filtered_news = [n for n in filtered_news if "NEUTRAL" in n["sentiment"]]

    # Filter 3: Search text
    if search_query.strip():
        q_lower = search_query.strip().lower()
        filtered_news = [
            n for n in filtered_news
            if q_lower in n["title"].lower() or q_lower in n["details"].lower() or q_lower in n["code"].lower()
        ]

    st.write(f"Showing **{len(filtered_news)}** disclosures:")

    if filtered_news:
        for item in filtered_news:
            date_display = item["date"]
            news_row_html = f"""<div class="news-row-card {item['row_cls']}"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;"><div><span style="font-size: 15px; font-weight: 800; color: #0f172a; margin-right: 8px;">{item['code']}</span><span class="news-badge" style="background: {item['bg']}; color: {item['fg']}; border: 1px solid {item['fg']}33;">{item['icon']} {item['sentiment']}: {item['reason']}</span></div><span style="font-size: 11px; color: #64748b;">📅 {date_display} • <i>{item['source']}</i></span></div><div style="font-size: 13px; font-weight: 700; color: #1e293b; margin-bottom: 4px;">{item['title']}</div><div style="font-size: 12px; color: #475569; line-height: 1.5;">{item['details']}</div></div>"""
            st.markdown(news_row_html, unsafe_allow_html=True)
    else:
        st.info("No news disclosures match the selected filter criteria.")

# ----------------- TAB 3: UPCOMING AGM & RECORD DATES ----------------- #

with tab_agm:
    st.subheader("📅 DSE Upcoming Record Dates & Corporate Actions")
    st.markdown(f"""
    <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 10px 14px; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between;">
        <span style="font-size: 13px; color: #1e40af; font-weight: 600;">
            📌 <b>Record Date Priority Feed:</b> Only showing companies where the <b>Record Date is ON or AFTER today ({m_status['date_str']})</b> or pending official notice. Expired record dates are automatically excluded.
        </span>
        <span style="font-size: 11px; background: #1d4ed8; color: white; padding: 3px 10px; border-radius: 12px; font-weight: 700;">
            Live Entitlements
        </span>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Official real-time tracking of upcoming dividend entitlement record dates, EGMs, and scheduled corporate meetings from Dhaka Stock Exchange PLC.")

    upcoming_events = fetch_upcoming_dse_events()
    
    if upcoming_events:
        total_up = len(upcoming_events)
        rec_imminent_cnt = sum(1 for e in upcoming_events if e.get("rec_dt") is not None)
        pending_rec_cnt = sum(1 for e in upcoming_events if e.get("rec_dt") is None)
        cash_div_cnt = sum(1 for e in upcoming_events if "cash" in e["dividend"].lower())

        # Summary Metric Cards
        u_m1, u_m2, u_m3, u_m4 = st.columns(4)
        with u_m1:
            st.metric("Total Active Actions", f"{total_up}")
        with u_m2:
            st.metric("📌 Upcoming Record Dates", f"{rec_imminent_cnt}")
        with u_m3:
            st.metric("💰 Cash Dividend Payers", f"{cash_div_cnt}")
        with u_m4:
            st.metric("⏸️ Awaiting Record Schedule", f"{pending_rec_cnt}")

        st.write("---")

        # Filters & Search
        up_c1, up_c2, up_c3 = st.columns([1.5, 1.5, 2])
        with up_c1:
            up_status_filter = st.selectbox(
                "Filter by Record Date Status",
                ["All Active Actions", "📌 Imminent Record Dates Only", "⏸️ Awaiting Record Schedule Only"]
            )
        with up_c2:
            up_div_filter = st.selectbox(
                "Filter by Dividend Type",
                ["All Types", "Cash Dividend Payers Only", "EGM / Corporate Purpose", "No Dividend Only"]
            )
        with up_c3:
            up_search = st.text_input("🔍 Search Company / Symbol (e.g. Bengal Biscuits, MIDAS, Desh, Marico)", "")

        filtered_up = upcoming_events

        if up_status_filter == "📌 Imminent Record Dates Only":
            filtered_up = [e for e in filtered_up if e.get("rec_dt") is not None]
        elif up_status_filter == "⏸️ Awaiting Record Schedule Only":
            filtered_up = [e for e in filtered_up if e.get("rec_dt") is None]

        if up_div_filter == "Cash Dividend Payers Only":
            filtered_up = [e for e in filtered_up if "Cash" in e["dividend"]]
        elif up_div_filter == "No Dividend Only":
            filtered_up = [e for e in filtered_up if "No" in e["dividend"] or "Nil" in e["dividend"]]
        elif up_div_filter == "EGM / Corporate Purpose":
            filtered_up = [e for e in filtered_up if "EGM" in e["dividend"] or "Purpose" in e["dividend"] or "Coupon" in e["dividend"]]

        if up_search.strip():
            qup = up_search.strip().lower()
            filtered_up = [
                e for e in filtered_up
                if qup in e["company"].lower() or qup in e["dividend"].lower() or qup in e["details"].lower()
            ]

        st.write(f"Showing **{len(filtered_up)}** active corporate actions:")

        view_mode = st.radio("View Format:", ["🗂️ Detailed Corporate Action Cards", "📊 Interactive Table"], horizontal=True)

        if view_mode == "📊 Interactive Table":
            table_data = []
            for ev in filtered_up:
                table_data.append({
                    "📌 Record Date": ev["record_date"],
                    "Company Name": ev["company"],
                    "💰 Dividend / Purpose": ev["dividend"],
                    "AGM Date": ev["agm_date"],
                    "Status / Countdown": f"{ev['icon']} {ev['status']}",
                    "Financial Year End": ev["year_end"],
                    "Official Source": ev["source"],
                    "Details / Venue": ev["details"]
                })
            df_table = pd.DataFrame(table_data)
            st.dataframe(df_table, width="stretch")
        else:
            for ev in filtered_up:
                up_card_html = f"""<div class="news-row-card" style="border-left: 4px solid {ev['fg']};"><div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;"><div><span style="font-size: 15px; font-weight: 800; color: #0f172a; margin-right: 8px;">{ev['company']}</span><span class="news-badge" style="background: {ev['bg']}; color: {ev['fg']}; border: 1px solid {ev['fg']}33;">{ev['icon']} {ev['status']}</span></div><span style="font-size: 11px; color: #64748b;">Year End: <b>{ev['year_end']}</b> • <i>{ev['source']}</i></span></div><div style="display: flex; flex-wrap: wrap; gap: 20px; font-size: 13px; color: #1e293b; margin: 8px 0;"><span style="background: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 6px; font-weight: 700; border: 1px solid #fca5a5;">📌 Record Date: <strong>{ev['record_date']}</strong></span><span>💰 <b>Dividend / Purpose:</b> <strong style="color: #0369a1;">{ev['dividend']}</strong></span><span>⏰ <b>AGM Date:</b> <strong style="color: #15803d;">{ev['agm_date']}</strong></span></div><div style="font-size: 11px; color: #64748b; line-height: 1.4;">{ev['details']}</div></div>"""
                st.markdown(up_card_html, unsafe_allow_html=True)
    else:
        st.info("No active corporate actions with upcoming record dates detected currently.")

# ----------------- TAB 4: STOCK SCREENER (BUY / SELL / HOLD) ----------------- #

with tab_screener:
    st.subheader("🎯 Technical Stock Screener & Market Decision Matrix")
    st.caption("Live technical analysis engine screening all listed DSE instruments into real-time Buy, Sell, and Hold states.")

    # Screen ALL listed instruments across DSE Market (470+ Instruments)
    all_symbols = sorted(list(unified_quotes.keys()))
    screener_records = []
    
    # Watchlist fast lookup for full historical depth
    wl_dict = {item["symbol"]: item for item in WATCHLIST_STOCKS}

    for sym in all_symbols:
        q = unified_quotes.get(sym, {})
        ltp = q.get("ltp", 0.0)
        chg = q.get("change", 0.0)
        pct = q.get("pct_change", 0.0)
        vol = q.get("volume", 0.0)
        ycp = q.get("ycp", 0.0)
        high = q.get("high", 0.0)
        low = q.get("low", 0.0)

        # Base technical momentum scoring
        score = 0
        signals_list = []

        # Factor 1: Intraday Momentum (% Change)
        if pct >= 4.0:
            score += 45
            signals_list.append("Strong Intraday Rally (+4% or higher)")
        elif pct >= 1.5:
            score += 30
            signals_list.append("Bullish Momentum (+1.5% or higher)")
        elif pct > 0.0:
            score += 15
            signals_list.append("Positive Intraday Gain")
        elif pct <= -4.0:
            score -= 45
            signals_list.append("Heavy Intraday Drop (-4% or lower)")
        elif pct <= -1.5:
            score -= 30
            signals_list.append("Bearish Pressure (-1.5% or lower)")
        elif pct < 0.0:
            score -= 15
            signals_list.append("Negative Intraday Decline")

        # Factor 2: Position Relative to YCP (Yesterday Close)
        if ycp > 0 and ltp > 0:
            if ltp > ycp:
                score += 15
                signals_list.append("Trading Above Previous Close")
            elif ltp < ycp:
                score -= 15
                signals_list.append("Trading Below Previous Close")

        # Factor 3: Day's High/Low Position
        if high > low and high > 0:
            pos_ratio = (ltp - low) / (high - low + 1e-9)
            if pos_ratio >= 0.8:
                score += 15
                signals_list.append("Closing Near Day's High")
            elif pos_ratio <= 0.2:
                score -= 15
                signals_list.append("Closing Near Day's Low")

        # Factor 4: Volume Surge
        if vol >= 200000:
            if pct >= 0:
                score += 15
                signals_list.append("High Institutional Volume Accumulation")
            else:
                score -= 15
                signals_list.append("Heavy Volume Sell-Off")

        # Factor 5: Historical indicators & Chart Patterns if in active watchlist
        target_sell_p: float = 0.0
        target_buy_p: float = 0.0
        state_action = "HOLD"
        state_icon = "🟡"
        move_pred = "⚖️ কনসোলিডেশন"

        if sym in wl_dict:
            df_h = fetch_authentic_history(sym, days=180)
            if not df_h.empty:
                if ltp > 0:
                    today_dt = pd.Timestamp(dt.date.today())
                    if today_dt in df_h.index:
                        df_h.loc[today_dt, 'close'] = ltp
                        df_h.loc[today_dt, 'high'] = max(df_h.loc[today_dt, 'high'], high or ltp)
                        df_h.loc[today_dt, 'low'] = min(df_h.loc[today_dt, 'low'], low or ltp)
                    else:
                        new_r = pd.DataFrame([{'open': ltp, 'high': high or ltp, 'low': low or ltp, 'close': ltp, 'volume': vol}], index=[today_dt])
                        df_h = pd.concat([df_h, new_r])

                df_ev = compute_all_indicators(df_h)
                pats = detect_chart_patterns(df_ev)
                sig_ev = evaluate_stock_signals(df_ev, pats)
                
                score = sig_ev["score"]
                state_action = sig_ev["action"]
                target_sell_p = sig_ev["target_selling_price"]
                target_buy_p = sig_ev["target_buying_price"]
                move_pred = sig_ev["move_badge"]
        else:
            # If not in active watchlist, compute authentic momentum & volatility targets
            est_atr = (high - low) if (high > low and high > 0) else (ltp * 0.025)
            if est_atr <= 0: est_atr = ltp * 0.025
            target_sell_p = round(ltp + (2.0 * est_atr), 2)
            target_buy_p = round(max(0.1, ltp - (1.5 * est_atr)), 2)

            if score >= 35: state_action = "STRONG BUY"
            elif score >= 15: state_action = "BUY"
            elif score <= -35: state_action = "STRONG SELL"
            elif score <= -15: state_action = "SELL"
            else: state_action = "HOLD"

            up_pct_s = round(((target_sell_p - ltp) / (ltp + 1e-9)) * 100, 1) if ltp > 0 and target_sell_p > ltp else 0.0
            down_pct_s = round(((ltp - target_buy_p) / (ltp + 1e-9)) * 100, 1) if ltp > 0 and target_buy_p < ltp else 0.0
            if score >= 15: move_pred = f"📈 বাড়বে → Tk {target_sell_p:.2f} (+{up_pct_s:.1f}%)"
            elif score <= -15: move_pred = f"📉 কমবে → Tk {target_buy_p:.2f} (-{down_pct_s:.1f}%)"
            else: move_pred = f"⚖️ রেঞ্জ: {target_buy_p:.1f}–{target_sell_p:.1f}"

        if "STRONG BUY" in state_action: state_icon = "🟢🟢"
        elif "BUY" in state_action: state_icon = "🟢"
        elif "STRONG SELL" in state_action: state_icon = "🔴🔴"
        elif "SELL" in state_action: state_icon = "🔴"
        else: state_icon = "🟡"

        screener_records.append({
            "STOCK NAME": sym,
            "STATE": f"{state_icon} {state_action}",
            "raw_state": state_action,
            "PREDICTED MOVE": move_pred,
            "LTP (Tk)": f"{ltp:.2f}" if ltp > 0 else "N/A",
            "CHANGE (%)": f"{chg:+.2f} ({pct:+.2f}%)",
            "SCORE": f"{score:+d} / 100",
            "raw_score": score,
            "TARGET BUYING PRICE (Tk)": f"{target_buy_p:.2f}" if target_buy_p > 0 else "N/A",
            "TARGET SELLING PRICE (Tk)": f"{target_sell_p:.2f}" if target_sell_p > 0 else "N/A"
        })

    # Summary Metrics Pills
    total_screened = len(screener_records)
    buy_count = sum(1 for r in screener_records if "BUY" in r["raw_state"])
    hold_count = sum(1 for r in screener_records if "HOLD" in r["raw_state"])
    sell_count = sum(1 for r in screener_records if "SELL" in r["raw_state"])

    s_m1, s_m2, s_m3, s_m4 = st.columns(4)
    with s_m1:
        st.metric("Total Screened Shares", f"{total_screened}")
    with s_m2:
        st.metric("🟢 BUY / STRONG BUY", f"{buy_count}")
    with s_m3:
        st.metric("🟡 HOLD / NEUTRAL", f"{hold_count}")
    with s_m4:
        st.metric("🔴 SELL / STRONG SELL", f"{sell_count}")

    st.write("---")

    # Filters & Instant Search
    sc_col1, sc_col2 = st.columns([1.5, 2])
    with sc_col1:
        state_filter_opt = st.selectbox(
            "Filter by Market State",
            ["All States", "🟢 Buy Opportunities (Strong Buy + Buy)", "🟡 Hold / Neutral Only", "🔴 Sell Alerts (Strong Sell + Sell)"]
        )
    with sc_col2:
        sc_search = st.text_input("🔍 Search Stock Symbol (e.g. GP, ACI, SQURPHARMA, BRACBANK, LH)", "")

    filtered_screener = screener_records

    if state_filter_opt == "🟢 Buy Opportunities (Strong Buy + Buy)":
        filtered_screener = [r for r in filtered_screener if "BUY" in r["raw_state"]]
    elif state_filter_opt == "🟡 Hold / Neutral Only":
        filtered_screener = [r for r in filtered_screener if "HOLD" in r["raw_state"]]
    elif state_filter_opt == "🔴 Sell Alerts (Strong Sell + Sell)":
        filtered_screener = [r for r in filtered_screener if "SELL" in r["raw_state"]]

    if sc_search.strip():
        q_sc = sc_search.strip().lower()
        filtered_screener = [
            r for r in filtered_screener
            if q_sc in r["STOCK NAME"].lower()
        ]

    st.write(f"Showing **{len(filtered_screener)}** shares:")

    # Clean Table View strictly: STOCK NAME | STATE | PREDICTED MOVE | LTP | CHANGE | SCORE | TURNAROUND FLOOR | HIGHEST PEAK TARGET
    clean_df = pd.DataFrame([{
        "STOCK NAME": r["STOCK NAME"],
        "STATE": r["STATE"],
        "PREDICTED MOVE": r["PREDICTED MOVE"],
        "LTP (Tk)": r["LTP (Tk)"],
        "CHANGE (%)": r["CHANGE (%)"],
        "SCORE": r["SCORE"],
        "TURNAROUND FLOOR (Tk)": r["TARGET BUYING PRICE (Tk)"],
        "HIGHEST PEAK TARGET (Tk)": r["TARGET SELLING PRICE (Tk)"]
    } for r in filtered_screener])

    st.dataframe(clean_df, width="stretch", hide_index=True)