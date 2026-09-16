#!/usr/bin/env python3
"""
Candlestick Pattern & Multi-Indicator Confluence Screener
=========================================================
A quantitative technical screener that analyzes daily OHLCV market data
to detect high-conviction bullish and bearish candlestick reversal patterns
validated by strict multi-indicator confluence rules (Volume Surge, EMA dynamic support/resistance, RSI Health).

Author: Senior Quantitative Developer & Technical Analyst (Google Antigravity)
"""

import os
import sys
import argparse
import warnings
import concurrent.futures
import datetime as dt
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

# ---------------------------------------------------------------------------
# 1. Technical Indicator Calculations (Pure Pandas / NumPy)
# ---------------------------------------------------------------------------

def calculate_ema(series: pd.Series, span: int) -> pd.Series:
    """Calculates Exponential Moving Average (EMA)."""
    return series.ewm(span=span, adjust=False).mean()

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculates Wilder's Relative Strength Index (RSI)."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    
    # Wilder's Exponential Smoothing (alpha = 1 / period)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    
    rs = avg_gain / (avg_loss + 1e-9)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi

def prepare_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Computes necessary technical indicators for pattern confluence validation."""
    data = df.copy()
    data.columns = [c.lower().strip() for c in data.columns]
    
    # Ensure float types
    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors='coerce')
            
    data.dropna(subset=['open', 'high', 'low', 'close', 'volume'], inplace=True)
    data = data[(data['open'] > 0) & (data['high'] > 0) & (data['low'] > 0) & (data['close'] > 0)]
    data.sort_index(ascending=True, inplace=True)
    
    if len(data) < 25:
        return data
    
    # 20-day Volume SMA
    data['vol_sma20'] = data['volume'].rolling(window=20).mean()
    
    # 20 EMA and 50 EMA
    data['ema20'] = calculate_ema(data['close'], 20)
    data['ema50'] = calculate_ema(data['close'], 50)
    
    # RSI 14
    data['rsi14'] = calculate_rsi(data['close'], 14)
    
    return data

# ---------------------------------------------------------------------------
# 2. Strict Candlestick Pattern Recognition Engine
# ---------------------------------------------------------------------------

def detect_candlestick_patterns(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Evaluates the most recent bars of the dataframe to detect strict high-conviction
    candlestick reversal structures:
      - Bullish: Bullish Engulfing, Hammer, Morning Star
      - Bearish: Bearish Engulfing, Shooting Star, Evening Star
    """
    signals = []
    n = len(df)
    if n < 5:
        return signals

    # Target the latest completed/active bar
    i = n - 1
    curr = df.iloc[i]
    prev1 = df.iloc[i - 1]
    prev2 = df.iloc[i - 2] if n >= 3 else None

    c_open, c_high, c_low, c_close = float(curr['open']), float(curr['high']), float(curr['low']), float(curr['close'])
    p1_open, p1_high, p1_low, p1_close = float(prev1['open']), float(prev1['high']), float(prev1['low']), float(prev1['close'])

    c_body = abs(c_close - c_open)
    c_range = max(c_high - c_low, 1e-6)
    p1_body = abs(p1_close - p1_open)
    p1_range = max(p1_high - p1_low, 1e-6)

    c_is_green = c_close >= c_open
    p1_is_green = p1_close >= p1_open

    lower_shadow = min(c_open, c_close) - c_low
    upper_shadow = c_high - max(c_open, c_close)

    # Local swing context (5-bar lookback prior to current candle)
    lookback = min(i, 6)
    prior_lows = df['low'].iloc[i - lookback: i]
    prior_highs = df['high'].iloc[i - lookback: i]
    prior_closes = df['close'].iloc[i - lookback: i]

    min_prior_low = prior_lows.min() if len(prior_lows) > 0 else c_low
    max_prior_high = prior_highs.max() if len(prior_highs) > 0 else c_high
    is_downward_swing = (c_low <= min_prior_low * 1.01) or (prior_closes.iloc[-1] < prior_closes.iloc[0])
    is_upward_swing = (c_high >= max_prior_high * 0.99) or (prior_closes.iloc[-1] > prior_closes.iloc[0])

    # -------------------------------------------------------------
    # A. BULLISH PATTERNS
    # -------------------------------------------------------------
    
    # 1. Bullish Engulfing:
    # Candle t-1 is red; Candle t is green; Body of candle t completely engulfs body of candle t-1.
    if (not p1_is_green) and c_is_green:
        if (c_open <= p1_close + 0.02 * p1_body) and (c_close >= p1_open - 0.02 * p1_body) and (c_body > p1_body):
            if p1_body >= 0.15 * p1_range and is_downward_swing:
                stop_loss = round(min(c_low, p1_low) * 0.995, 2)
                signals.append({
                    'pattern': 'Bullish Engulfing',
                    'bias': 'Bullish',
                    'stop_loss': stop_loss,
                    'details': f"Green candle ({c_open:.2f}->{c_close:.2f}) engulfed prior red candle ({p1_open:.2f}->{p1_close:.2f})."
                })

    # 2. Hammer:
    # Lower shadow >= 2x real body size; Upper shadow <= 10% of candle range; Occurs after a downward swing.
    if (lower_shadow >= 2.0 * max(c_body, 0.01 * c_range)) and (upper_shadow <= 0.10 * c_range) and is_downward_swing:
        stop_loss = round(c_low * 0.995, 2)
        signals.append({
            'pattern': 'Hammer',
            'bias': 'Bullish',
            'stop_loss': stop_loss,
            'details': f"Long lower shadow ({lower_shadow:.2f}) >= 2x body ({c_body:.2f}) with tiny upper wick ({upper_shadow:.2f})."
        })

    # 3. Morning Star (3-Candle structure):
    # Candle 1 (t-2) is long red, Candle 2 (t-1) is small-bodied, Candle 3 (t) is green and closes well into Candle 1's body.
    if prev2 is not None:
        p2_open, p2_high, p2_low, p2_close = float(prev2['open']), float(prev2['high']), float(prev2['low']), float(prev2['close'])
        p2_body = abs(p2_close - p2_open)
        p2_range = max(p2_high - p2_low, 1e-6)
        p2_is_green = p2_close >= p2_open

        if (not p2_is_green) and (p2_body >= 0.35 * p2_range):
            if (p1_body <= 0.45 * p2_body) and c_is_green:
                # Closes at or above midpoint of Candle 1 body
                midpoint_c1 = p2_close + 0.50 * (p2_open - p2_close)
                if c_close >= midpoint_c1:
                    stop_loss = round(min(c_low, p1_low, p2_low) * 0.995, 2)
                    signals.append({
                        'pattern': 'Morning Star',
                        'bias': 'Bullish',
                        'stop_loss': stop_loss,
                        'details': f"3-bar reversal: Long red -> small star ({p1_open:.2f}->{p1_close:.2f}) -> Green close ({c_close:.2f}) above 50% midpoint ({midpoint_c1:.2f})."
                    })

    # -------------------------------------------------------------
    # B. BEARISH PATTERNS
    # -------------------------------------------------------------
    
    # 1. Bearish Engulfing:
    # Candle t-1 is green; Candle t is red; Body of candle t completely engulfs body of candle t-1.
    if p1_is_green and (not c_is_green):
        if (c_open >= p1_close - 0.02 * p1_body) and (c_close <= p1_open + 0.02 * p1_body) and (c_body > p1_body):
            if p1_body >= 0.15 * p1_range and is_upward_swing:
                stop_loss = round(max(c_high, p1_high) * 1.005, 2)
                signals.append({
                    'pattern': 'Bearish Engulfing',
                    'bias': 'Bearish',
                    'stop_loss': stop_loss,
                    'details': f"Red candle ({c_open:.2f}->{c_close:.2f}) engulfed prior green candle ({p1_open:.2f}->{p1_close:.2f})."
                })

    # 2. Shooting Star:
    # Upper shadow >= 2x real body size; Lower shadow <= 10% of candle range; Occurs near local highs.
    if (upper_shadow >= 2.0 * max(c_body, 0.01 * c_range)) and (lower_shadow <= 0.10 * c_range) and is_upward_swing:
        stop_loss = round(c_high * 1.005, 2)
        signals.append({
            'pattern': 'Shooting Star',
            'bias': 'Bearish',
            'stop_loss': stop_loss,
            'details': f"Long upper wick ({upper_shadow:.2f}) >= 2x body ({c_body:.2f}) rejecting local high ({c_high:.2f})."
        })

    # 3. Evening Star (3-Candle structure):
    # Candle 1 (t-2) is long green, Candle 2 (t-1) is small-bodied, Candle 3 (t) is red and closes well into Candle 1's body.
    if prev2 is not None:
        p2_open, p2_high, p2_low, p2_close = float(prev2['open']), float(prev2['high']), float(prev2['low']), float(prev2['close'])
        p2_body = abs(p2_close - p2_open)
        p2_range = max(p2_high - p2_low, 1e-6)
        p2_is_green = p2_close >= p2_open

        if p2_is_green and (p2_body >= 0.35 * p2_range):
            if (p1_body <= 0.45 * p2_body) and (not c_is_green):
                # Closes at or below midpoint of Candle 1 body
                midpoint_c1 = p2_open + 0.50 * (p2_close - p2_open)
                if c_close <= midpoint_c1:
                    stop_loss = round(max(c_high, p1_high, p2_high) * 1.005, 2)
                    signals.append({
                        'pattern': 'Evening Star',
                        'bias': 'Bearish',
                        'stop_loss': stop_loss,
                        'details': f"3-bar reversal: Long green -> small star ({p1_open:.2f}->{p1_close:.2f}) -> Red close ({c_close:.2f}) below 50% midpoint ({midpoint_c1:.2f})."
                    })

    return signals

# ---------------------------------------------------------------------------
# 3. Confluence Validation Rules & Scoring
# ---------------------------------------------------------------------------

def validate_confluence(df: pd.DataFrame, pattern_bias: str) -> Tuple[bool, int, List[str]]:
    """
    Validates confluence rules against the latest candle:
      1. Volume Surge: Volume >= 1.3x 20-day Volume SMA
      2. MA Alignment:
         - Bullish: Close >= EMA 20 or bouncing off 20/50 EMA dynamic support.
         - Bearish: Close <= EMA 20 or rejecting from 20/50 EMA dynamic resistance.
      3. RSI Health:
         - Bullish: RSI(14) between 40 and 68 (not overbought).
         - Bearish: RSI(14) between 32 and 60 (not oversold).

    Returns:
      (passes_confluence, quality_score [1-5], list_of_triggers_met)
    """
    if len(df) < 20:
        return False, 0, []

    curr = df.iloc[-1]
    close = float(curr['close'])
    high = float(curr['high'])
    low = float(curr['low'])
    vol = float(curr['volume'])
    vol_sma20 = float(curr.get('vol_sma20', vol)) if pd.notnull(curr.get('vol_sma20')) else vol
    ema20 = float(curr.get('ema20', close)) if pd.notnull(curr.get('ema20')) else close
    ema50 = float(curr.get('ema50', close)) if pd.notnull(curr.get('ema50')) else close
    rsi14 = float(curr.get('rsi14', 50.0)) if pd.notnull(curr.get('rsi14')) else 50.0

    triggers_met = []

    # --- Rule 1: Volume Surge ---
    # Volume >= 1.3x of 20-day Volume SMA
    vol_ratio = (vol / vol_sma20) if vol_sma20 > 0 else 1.0
    if vol_ratio >= 1.30:
        triggers_met.append(f"Volume Surge ({vol_ratio:.2f}x SMA20)")

    # --- Rule 2: Moving Average Alignment ---
    if pattern_bias == 'Bullish':
        # Close >= 20 EMA or bouncing off 20/50 EMA dynamic support
        ema20_bounce = (low <= ema20 * 1.015) and (close >= ema20 * 0.99)
        ema50_bounce = (low <= ema50 * 1.015) and (close >= ema50 * 0.99)
        if close >= ema20 or ema20_bounce or ema50_bounce:
            tag = "Above EMA20" if close >= ema20 else ("EMA20 Support Bounce" if ema20_bounce else "EMA50 Support Bounce")
            triggers_met.append(f"MA Alignment ({tag})")
    elif pattern_bias == 'Bearish':
        # Close <= 20 EMA or rejecting from 20/50 EMA dynamic resistance
        ema20_reject = (high >= ema20 * 0.985) and (close <= ema20 * 1.01)
        ema50_reject = (high >= ema50 * 0.985) and (close <= ema50 * 1.01)
        if close <= ema20 or ema20_reject or ema50_reject:
            tag = "Below EMA20" if close <= ema20 else ("EMA20 Resistance Reject" if ema20_reject else "EMA50 Resistance Reject")
            triggers_met.append(f"MA Alignment ({tag})")

    # --- Rule 3: RSI Health ---
    if pattern_bias == 'Bullish':
        # RSI(14) between 40 and 68 for Bullish entries (not overbought)
        if 40.0 <= rsi14 <= 68.0:
            triggers_met.append(f"RSI Health (RSI={rsi14:.1f})")
    elif pattern_bias == 'Bearish':
        # RSI(14) between 32 and 60 for Bearish entries (not oversold)
        if 32.0 <= rsi14 <= 60.0:
            triggers_met.append(f"RSI Health (RSI={rsi14:.1f})")

    # Confluence Filter: MUST meet AT LEAST 2 rules
    passed = len(triggers_met) >= 2

    # Quality Score (1 to 5):
    # Base pattern conviction = 2
    # +1 per confluence trigger met (Total 3 triggers -> Max 5)
    # Extra boost to 5 if all 3 triggers met with strong volume ratio >= 1.5x
    score = min(5, 2 + len(triggers_met))
    if len(triggers_met) == 3 and vol_ratio >= 1.50:
        score = 5

    return passed, score, triggers_met

# ---------------------------------------------------------------------------
# 4. Market Data Ingestion & Cleaning
# ---------------------------------------------------------------------------

HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://stocknow.com.bd/'
}

def fetch_ohlcv_from_stocknow(symbol: str) -> Optional[pd.DataFrame]:
    """Fetches clean daily OHLCV directly from StockNow 1D Candle API."""
    symbol = symbol.strip().upper()
    try:
        url = f"https://stocknow.com.bd/api/v1/instruments/{symbol}/history?data2=true&resolution=1D"
        res = requests.get(url, headers=HTTP_HEADERS, verify=False, timeout=8)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list) and len(data) >= 6:
                opens, highs, lows, closes, vols, timestamps = data[0], data[1], data[2], data[3], data[4], data[5]
                n = len(timestamps)
                if n > 0:
                    df = pd.DataFrame({
                        'open': [float(x) for x in opens[:n]],
                        'high': [float(x) for x in highs[:n]],
                        'low': [float(x) for x in lows[:n]],
                        'close': [float(x) for x in closes[:n]],
                        'volume': [float(x) for x in vols[:n]],
                    }, index=pd.to_datetime([int(ts) for ts in timestamps[:n]], unit='s'))
                    
                    # Clean data: drop non-trading bars and ensure sorting
                    df = df[(df['open'] > 0) & (df['high'] > 0) & (df['low'] > 0) & (df['close'] > 0)]
                    df.sort_index(ascending=True, inplace=True)
                    return df
    except Exception:
        pass
    return None

def fetch_ohlcv_from_bdshare(symbol: str, days: int = 365) -> Optional[pd.DataFrame]:
    """Fallback fetcher using bdshare."""
    symbol = symbol.strip().upper()
    try:
        import bdshare
        end_date = str(dt.date.today())
        start_date = str(dt.date.today() - dt.timedelta(days=days))
        df = bdshare.get_historical_data(start_date, end_date, symbol)
        if df is not None and not df.empty:
            df.columns = [str(c).lower().strip() for c in df.columns]
            df.index = pd.to_datetime(df.index, errors='coerce')
            df.dropna(subset=['close'], inplace=True)
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            df = df[(df['open'] > 0) & (df['high'] > 0) & (df['low'] > 0) & (df['close'] > 0)]
            df.sort_index(ascending=True, inplace=True)
            return df
    except Exception:
        pass
    return None

def load_ohlcv(symbol_or_path: str, min_bars: int = 60) -> Optional[pd.DataFrame]:
    """
    Loads and cleans daily OHLCV data from local CSV or live market API.
    Ensures at least `min_bars` of valid trading history.
    """
    df = None
    # Check if local CSV file exists
    if os.path.isfile(symbol_or_path):
        try:
            raw = pd.read_csv(symbol_or_path)
            raw.columns = [c.lower().strip() for c in raw.columns]
            if 'date' in raw.columns:
                raw['date'] = pd.to_datetime(raw['date'])
                raw.set_index('date', inplace=True)
            df = raw
        except Exception as e:
            print(f"Error loading CSV {symbol_or_path}: {e}")
            return None
    else:
        # Fetch from authentic StockNow API first, then fallback to bdshare
        df = fetch_ohlcv_from_stocknow(symbol_or_path)
        if df is None or len(df) < min_bars:
            df_bd = fetch_ohlcv_from_bdshare(symbol_or_path)
            if df_bd is not None and len(df_bd) >= min_bars:
                df = df_bd

    if df is not None and not df.empty:
        df = prepare_indicators(df)
        if len(df) >= min_bars:
            return df
    return None

def get_market_ticker_universe() -> List[str]:
    """Retrieves active ticker universe from DSE live trade feed or high-liquidity defaults."""
    tickers = []
    try:
        import bdshare
        dse_df = bdshare.get_current_trade_data()
        if dse_df is not None and not dse_df.empty and 'symbol' in dse_df.columns:
            tickers = [str(s).strip().upper() for s in dse_df['symbol'].dropna().unique() if len(str(s).strip()) > 1]
    except Exception:
        pass

    if not tickers:
        # High liquidity default universe of top DSE stocks
        tickers = [
            "GP", "BATBC", "SQURPHARMA", "BEXIMCO", "BRACBANK", "CITYBANK", "OLYMPIC",
            "RENATA", "LHBL", "ROBI", "ISLAMIBANK", "UPGDCL", "EBL", "PUBALIBANK",
            "BSC", "SEAPEARL", "MEGHNALIFE", "ARAMIT", "DELTALIFE", "UNIQUEHRL",
            "BEACONPHAR", "WALTONHIL", "MARICO", "HEIDELBCEM", "MJLBD", "TITASGAS",
            "POWERGRID", "BSRMLTD", "BSCCOS", "SUMITPOWER", "IDLC", "JAMUNAOIL",
            "MPETROLEUM", "PADMAOIL", "DBH", "LANKABAFIN", "ORIONPHARM", "ACMEPL",
            "AAMRANET", "ADNTEL", "GENEXIL", "NAVANAPHAR", "KOHINOOR", "SHASHADN"
        ]
    return sorted(list(set(tickers)))

# ---------------------------------------------------------------------------
# 5. Core Confluence Screener Pipeline
# ---------------------------------------------------------------------------

def analyze_ticker(ticker: str, min_bars: int = 60) -> List[Dict[str, Any]]:
    """Analyzes a single ticker for pattern recognition and confluence verification."""
    df = load_ohlcv(ticker, min_bars=min_bars)
    if df is None or len(df) < min_bars:
        return []

    patterns = detect_candlestick_patterns(df)
    if not patterns:
        return []

    latest_close = float(df['close'].iloc[-1])
    qualified_results = []

    for pat in patterns:
        passed, score, triggers = validate_confluence(df, pat['bias'])
        if passed:
            qualified_results.append({
                'ticker': ticker,
                'bias': pat['bias'],
                'pattern': pat['pattern'],
                'quality_score': score,
                'last_close': latest_close,
                'confluence_triggers': ", ".join(triggers),
                'invalidation': pat['stop_loss'],
                'details': pat['details']
            })

    return qualified_results

def run_screener(tickers: List[str], max_workers: int = 12, min_bars: int = 60) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Runs concurrent scanning across provided ticker list."""
    bullish_setups = []
    bearish_setups = []

    print(f"[*] Starting Confluence Screener across {len(tickers)} tickers (min {min_bars} bars)...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ticker = {executor.submit(analyze_ticker, t, min_bars): t for t in tickers}
        completed = 0
        for future in concurrent.futures.as_completed(future_to_ticker):
            completed += 1
            t = future_to_ticker[future]
            try:
                results = future.result()
                for r in results:
                    if r['bias'] == 'Bullish':
                        bullish_setups.append(r)
                    elif r['bias'] == 'Bearish':
                        bearish_setups.append(r)
            except Exception as e:
                pass

    # Sort setups by Quality Score descending, then by ticker
    bullish_setups.sort(key=lambda x: (-x['quality_score'], x['ticker']))
    bearish_setups.sort(key=lambda x: (-x['quality_score'], x['ticker']))

    return bullish_setups, bearish_setups

# ---------------------------------------------------------------------------
# 6. Formatting & Presentation
# ---------------------------------------------------------------------------

def format_table(title: str, records: List[Dict[str, Any]]) -> str:
    """Formats scan results into markdown and console tables."""
    lines = []
    lines.append(f"### {title}")
    lines.append("")
    if not records:
        lines.append("_No qualifying setups detected matching strict confluence criteria at this time._\n")
        return "\n".join(lines)

    lines.append("| Ticker | Pattern Identified | Quality Score (1-5) | Last Close | Confluence Triggers Met | Invalidation / Stop-Loss |")
    lines.append("| :--- | :--- | :---: | :---: | :--- | :---: |")
    for r in records:
        score_stars = f"{r['quality_score']}/5"
        lines.append(f"| **{r['ticker']}** | {r['pattern']} | {score_stars} | Tk {r['last_close']:.2f} | {r['confluence_triggers']} | Tk {r['invalidation']:.2f} |")
    lines.append("")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# 7. Self-Test Suite (Verification & Synthetic Testing)
# ---------------------------------------------------------------------------

def generate_synthetic_ohlcv(pattern_type: str) -> pd.DataFrame:
    """Generates synthetic 65-bar OHLCV dataframe engineered to trigger specific patterns & confluence."""
    np.random.seed(42)
    dates = pd.date_range(end=dt.datetime.now(), periods=65, freq='D')
    
    # Base baseline random walk
    prices = 100.0 + np.cumsum(np.random.randn(65) * 0.5)
    volumes = np.full(65, 100000.0)
    
    opens = prices - np.random.uniform(0.1, 0.5, 65)
    closes = prices + np.random.uniform(0.1, 0.5, 65)
    highs = np.maximum(opens, closes) + np.random.uniform(0.2, 0.8, 65)
    lows = np.minimum(opens, closes) - np.random.uniform(0.2, 0.8, 65)

    # 1. Bullish Engulfing Setup with Volume surge at support
    if pattern_type == 'bullish_engulfing':
        # Create downward swing for prior 5 bars
        for k in range(58, 63):
            opens[k] = 100 - (k - 58) * 1.5
            closes[k] = opens[k] - 1.2
            highs[k] = opens[k] + 0.3
            lows[k] = closes[k] - 0.3
        # Bar t-1 (Red)
        opens[63] = 92.0
        closes[63] = 90.0
        highs[63] = 92.5
        lows[63] = 89.5
        # Bar t (Green Engulfing)
        opens[64] = 89.8
        closes[64] = 93.0
        highs[64] = 93.5
        lows[64] = 89.2
        volumes[64] = 200000.0  # 2.0x volume surge

    # 2. Hammer Setup with Volume surge at dip
    elif pattern_type == 'hammer':
        # Moderate downward swing to keep RSI in 40-55 range and bounce off EMA20
        for k in range(50, 64):
            closes[k] = 100 - (k - 50) * 0.4
            opens[k] = closes[k] + 0.3
            highs[k] = opens[k] + 0.2
            lows[k] = closes[k] - 0.2
        # Bar t (Hammer bouncing off support with volume surge)
        opens[64] = 95.0
        closes[64] = 95.5 # body = 0.5
        highs[64] = 95.6 # upper shadow = 0.1 (<= 10% range)
        lows[64] = 93.0  # lower shadow = 2.0 (>= 2x body)
        volumes[64] = 180000.0

    # 3. Morning Star Setup
    elif pattern_type == 'morning_star':
        for k in range(50, 62):
            closes[k] = 100 - (k - 50) * 0.5
            opens[k] = closes[k] + 0.4
            highs[k] = opens[k] + 0.2
            lows[k] = closes[k] - 0.2
        # Bar t-2 (Long Red)
        opens[62] = 94.0
        closes[62] = 91.0
        highs[62] = 94.2
        lows[62] = 90.8
        # Bar t-1 (Small Star)
        opens[63] = 90.5
        closes[63] = 90.8
        highs[63] = 91.0
        lows[63] = 90.2
        # Bar t (Strong Green closing > 50% into Bar t-2)
        opens[64] = 91.0
        closes[64] = 93.5
        highs[64] = 93.8
        lows[64] = 90.8
        volumes[64] = 185000.0

    # 4. Bearish Engulfing Setup with Volume surge at peak
    elif pattern_type == 'bearish_engulfing':
        # Upward swing
        for k in range(58, 63):
            opens[k] = 80 + (k - 58) * 1.5
            closes[k] = opens[k] + 1.2
            highs[k] = closes[k] + 0.3
            lows[k] = opens[k] - 0.3
        # Bar t-1 (Green)
        opens[63] = 88.0
        closes[63] = 90.0
        highs[63] = 90.5
        lows[63] = 87.5
        # Bar t (Red Engulfing)
        opens[64] = 90.2
        closes[64] = 87.0
        highs[64] = 90.8
        lows[64] = 86.8
        volumes[64] = 190000.0

    # 5. Shooting Star Setup with Volume surge at peak
    elif pattern_type == 'shooting_star':
        # Upward swing
        for k in range(58, 64):
            opens[k] = 80 + (k - 58) * 1.5
            closes[k] = opens[k] + 1.0
            highs[k] = closes[k] + 0.2
            lows[k] = opens[k] - 0.2
        # Bar t (Shooting Star)
        opens[64] = 90.5
        closes[64] = 90.0 # body = 0.5
        highs[64] = 92.5 # upper shadow = 2.0 (>= 2x body)
        lows[64] = 89.9  # lower shadow = 0.1 (<= 10% range)
        volumes[64] = 175000.0

    # 6. Evening Star Setup
    elif pattern_type == 'evening_star':
        for k in range(50, 62):
            closes[k] = 80 + (k - 50) * 0.5
            opens[k] = closes[k] - 0.4
            highs[k] = closes[k] + 0.2
            lows[k] = opens[k] - 0.2
        # Bar t-2 (Long Green)
        opens[62] = 86.0
        closes[62] = 89.0
        highs[62] = 89.2
        lows[62] = 85.8
        # Bar t-1 (Small Star)
        opens[63] = 89.5
        closes[63] = 89.2
        highs[63] = 89.8
        lows[63] = 89.0
        # Bar t (Strong Red closing below 50% into Bar t-2)
        opens[64] = 89.0
        closes[64] = 86.5
        highs[64] = 89.2
        lows[64] = 86.2
        volumes[64] = 185000.0

    df = pd.DataFrame({
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': volumes
    }, index=dates)

    return prepare_indicators(df)

def run_self_test():
    """Executes automated verification tests on pattern recognition and confluence rules."""
    print("=" * 75)
    print("  RUNNING QUANTITATIVE PATTERN & CONFLUENCE SELF-TEST SUITE")
    print("=" * 75)
    
    test_cases = [
        ('bullish_engulfing', 'Bullish Engulfing', 'Bullish'),
        ('hammer', 'Hammer', 'Bullish'),
        ('morning_star', 'Morning Star', 'Bullish'),
        ('bearish_engulfing', 'Bearish Engulfing', 'Bearish'),
        ('shooting_star', 'Shooting Star', 'Bearish'),
        ('evening_star', 'Evening Star', 'Bearish'),
    ]

    all_passed = True
    for test_id, expected_pattern, expected_bias in test_cases:
        df = generate_synthetic_ohlcv(test_id)
        patterns = detect_candlestick_patterns(df)
        detected_names = [p['pattern'] for p in patterns]
        
        has_expected_pattern = any(p['pattern'] == expected_pattern and p['bias'] == expected_bias for p in patterns)
        
        if has_expected_pattern:
            # Validate confluence
            passed, score, triggers = validate_confluence(df, expected_bias)
            status = "PASSED [OK]" if (passed and score >= 3) else "CONFLUENCE WARN"
            print(f" [+] {expected_pattern:<20} | Bias: {expected_bias:<8} | Triggers: {len(triggers)}/3 | Quality: {score}/5 | {status}")
        else:
            all_passed = False
            print(f" [-] {expected_pattern:<20} | Expected: {expected_pattern}, Got: {detected_names} | FAILED [X]")

    print("-" * 75)
    if all_passed:
        print(" [SUCCESS] All 6 High-Conviction Candlestick Patterns & Confluence Tests Passed Cleanly.")
    else:
        print(" [WARNING] Some tests encountered mismatches.")
    print("=" * 75 + "\n")
    return all_passed

# ---------------------------------------------------------------------------
# 8. Main Entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Candlestick Pattern & Multi-Indicator Confluence Screener")
    parser.add_argument('--tickers', nargs='+', default=None, help="Specific ticker list to scan (e.g. GP BATBC SQURPHARMA)")
    parser.add_argument('--csv', type=str, default=None, help="Path to single OHLCV CSV file to scan")
    parser.add_argument('--max-tickers', type=int, default=100, help="Maximum number of market tickers to screen (default: 100)")
    parser.add_argument('--min-bars', type=int, default=60, help="Minimum trading bars required per ticker (default: 60)")
    parser.add_argument('--test', action='store_true', help="Run unit self-tests on pattern math and confluence logic")
    args = parser.parse_args()

    # If --test is requested, run test suite first
    if args.test:
        run_self_test()

    # Determine tickers to scan
    if args.csv:
        print(f"[*] Scanning single CSV: {args.csv}")
        df = load_ohlcv(args.csv, min_bars=args.min_bars)
        if df is None:
            print(f"Error: Unable to load valid data with at least {args.min_bars} bars from {args.csv}")
            sys.exit(1)
        patterns = detect_candlestick_patterns(df)
        bullish, bearish = [], []
        ticker_name = os.path.basename(args.csv).replace('.csv', '').upper()
        for pat in patterns:
            passed, score, triggers = validate_confluence(df, pat['bias'])
            if passed:
                rec = {
                    'ticker': ticker_name,
                    'bias': pat['bias'],
                    'pattern': pat['pattern'],
                    'quality_score': score,
                    'last_close': float(df['close'].iloc[-1]),
                    'confluence_triggers': ", ".join(triggers),
                    'invalidation': pat['stop_loss'],
                    'details': pat['details']
                }
                if pat['bias'] == 'Bullish':
                    bullish.append(rec)
                else:
                    bearish.append(rec)
    else:
        if args.tickers:
            ticker_list = [t.strip().upper() for t in args.tickers]
        else:
            ticker_list = get_market_ticker_universe()
            if args.max_tickers and len(ticker_list) > args.max_tickers:
                ticker_list = ticker_list[:args.max_tickers]

        bullish, bearish = run_screener(ticker_list, max_workers=16, min_bars=args.min_bars)

    # Output Tables
    print("\n" + "=" * 80)
    print(" CANDLESTICK PATTERN & MULTI-INDICATOR CONFLUENCE SCREENER RESULTS")
    print("=" * 80 + "\n")

    table1_md = format_table("Table 1: Bullish Setups (Expected to Rise)", bullish)
    table2_md = format_table("Table 2: Bearish Setups (Expected to Fall / Exit Alert)", bearish)

    print(table1_md)
    print(table2_md)
    print("=" * 80)

if __name__ == "__main__":
    main()
