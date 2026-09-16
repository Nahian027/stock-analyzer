"""
StockNow Technical Trade Signal Automation Agent (stocknow_agent.py)
Fetches live & historical technical indicator data for DSE tickers from StockNow,
computes quantitative metrics, and generates standardized Technical Trade Signal Reports.
"""

import sys
import os
import argparse
import requests
import urllib3
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://stocknow.com.bd/'
}


def fetch_ticker_data_stocknow(ticker: str) -> Optional[pd.DataFrame]:
    """
    Extracts raw OHLCV historical bars from StockNow 1D REST API.
    Fallback to bdshare if StockNow API is temporarily unreachable.
    """
    sym = ticker.strip().upper()
    url = f"https://stocknow.com.bd/api/v1/instruments/{sym}/history?data2=true&resolution=1D"
    
    try:
        res = requests.get(url, headers=HTTP_HEADERS, verify=False, timeout=10)
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
                    
                    df = df[(df['open'] > 0) & (df['high'] > 0) & (df['low'] > 0) & (df['close'] > 0)]
                    df.sort_index(ascending=True, inplace=True)
                    if len(df) >= 10:
                        return df
    except Exception as e:
        pass

    # Fallback to bdshare
    try:
        import bdshare
        import datetime as dt
        start_date = str(dt.date.today() - dt.timedelta(days=730))
        end_date = str(dt.date.today())
        df_bd = bdshare.get_historical_data(start_date, end_date, sym)
        if df_bd is not None and not df_bd.empty:
            df_bd.columns = [str(c).lower().strip() for c in df_bd.columns]
            df_bd.index = pd.to_datetime(df_bd.index, errors='coerce')
            df_bd.dropna(subset=['close'], inplace=True)
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df_bd.columns:
                    df_bd[col] = pd.to_numeric(df_bd[col], errors='coerce')
            df_bd = df_bd[(df_bd['open'] > 0) & (df_bd['high'] > 0) & (df_bd['low'] > 0) & (df_bd['close'] > 0)]
            df_bd.sort_index(ascending=True, inplace=True)
            if len(df_bd) >= 10:
                return df_bd
    except Exception:
        pass

    return None


def calculate_technical_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes all standard indicators:
    - LTP, 20 SMA, 50 SMA, 200 SMA
    - RSI(14)
    - MACD (12, 26, 9): Line, Signal, Histogram
    - 20-day Average Volume & Volume Multiplier
    - Key Price Levels (Entry, Target, Stop Loss)
    """
    close_s = df['close']
    high_s = df['high']
    low_s = df['low']
    vol_s = df['volume']
    
    ltp = round(float(close_s.iloc[-1]), 2)
    prev_close = round(float(close_s.iloc[-2]), 2) if len(close_s) >= 2 else ltp
    is_green_day = (ltp >= prev_close)

    # 1. Moving Averages
    sma_20 = float(close_s.rolling(20, min_periods=min(5, len(close_s))).mean().iloc[-1])
    sma_50 = float(close_s.rolling(50, min_periods=min(10, len(close_s))).mean().iloc[-1]) if len(close_s) >= 20 else sma_20
    sma_200 = float(close_s.rolling(200, min_periods=min(30, len(close_s))).mean().iloc[-1]) if len(close_s) >= 50 else sma_50
    golden_cross = (sma_50 > sma_200)

    # 2. RSI (14)
    delta = close_s.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(14, min_periods=min(3, len(close_s))).mean()
    avg_loss = loss.rolling(14, min_periods=min(3, len(close_s))).mean()
    
    # Wilder smoothing
    if len(close_s) > 14:
        for i in range(14, len(close_s)):
            avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * 13 + gain.iloc[i]) / 14
            avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * 13 + loss.iloc[i]) / 14
            
    last_gain = float(avg_gain.iloc[-1]) if pd.notnull(avg_gain.iloc[-1]) else 0.0
    last_loss = float(avg_loss.iloc[-1]) if pd.notnull(avg_loss.iloc[-1]) else 0.0
    
    if last_loss == 0.0:
        rsi_14 = 100.0 if last_gain > 0 else 50.0
    else:
        rs = last_gain / (last_loss + 1e-9)
        rsi_14 = float(np.clip(100.0 - (100.0 / (1.0 + rs)), 0.0, 100.0))

    # 3. MACD (12, 26, 9)
    ema_12 = close_s.ewm(span=12, adjust=False).mean()
    ema_26 = close_s.ewm(span=26, adjust=False).mean()
    macd_line = ema_12 - ema_26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_hist = macd_line - signal_line
    
    curr_macd = float(macd_line.iloc[-1])
    curr_signal = float(signal_line.iloc[-1])
    curr_hist = float(macd_hist.iloc[-1])
    prev_hist = float(macd_hist.iloc[-2]) if len(macd_hist) >= 2 else curr_hist
    hist_expanding = (curr_hist > prev_hist)

    # 4. Volume & Breakout
    vol_20_sma = float(vol_s.rolling(20, min_periods=min(3, len(vol_s))).mean().iloc[-1])
    curr_vol = float(vol_s.iloc[-1])
    vol_ratio = curr_vol / (vol_20_sma + 1e-9)
    
    # 20-day high breakout check
    high_20 = float(high_s.tail(min(20, len(high_s))).iloc[:-1].max()) if len(high_s) > 20 else ltp
    is_breakout = (ltp > high_20) and (vol_ratio >= 1.2)

    # 5. ATR(14) for Key Levels
    tr = pd.concat([
        high_s - low_s,
        (high_s - close_s.shift(1)).abs(),
        (low_s - close_s.shift(1)).abs()
    ], axis=1).max(axis=1)
    atr = float(tr.rolling(14, min_periods=min(3, len(df))).mean().iloc[-1])
    if pd.isna(atr) or atr <= 0:
        atr = max(0.5, ltp * 0.02)

    # Key Levels
    entry_price = ltp
    target_price = round(ltp + max(1.5 * atr, ltp * 0.035), 2)
    stop_loss = round(max(0.1, ltp - max(1.0 * atr, ltp * 0.025)), 2)

    return {
        "ltp": ltp,
        "prev_close": prev_close,
        "is_green_day": is_green_day,
        "sma_20": round(sma_20, 2),
        "sma_50": round(sma_50, 2),
        "sma_200": round(sma_200, 2),
        "golden_cross": golden_cross,
        "rsi_14": round(rsi_14, 2),
        "macd_line": round(curr_macd, 3),
        "signal_line": round(curr_signal, 3),
        "macd_hist": round(curr_hist, 3),
        "hist_expanding": hist_expanding,
        "vol_20_sma": int(vol_20_sma),
        "curr_vol": int(curr_vol),
        "vol_ratio": round(vol_ratio, 2),
        "is_breakout": is_breakout,
        "entry_price": entry_price,
        "target_price": target_price,
        "stop_loss": stop_loss
    }


def compute_technical_score(tech: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes Technical Scoring (Out of 100) per specifications:
    - Moving Averages (30 pts)
    - RSI (25 pts)
    - MACD (20 pts)
    - Volume & Price Action (25 pts)
    """
    ltp = tech["ltp"]
    sma_20 = tech["sma_20"]
    sma_50 = tech["sma_50"]
    sma_200 = tech["sma_200"]
    golden_cross = tech["golden_cross"]
    rsi = tech["rsi_14"]
    macd_line = tech["macd_line"]
    signal_line = tech["signal_line"]
    macd_hist = tech["macd_hist"]
    hist_expanding = tech["hist_expanding"]
    vol_ratio = tech["vol_ratio"]
    is_green_day = tech["is_green_day"]
    is_breakout = tech["is_breakout"]

    # 1. Moving Averages (30 pts)
    ma_score = 0
    if ltp > sma_20 and ltp > sma_50 and ltp > sma_200:
        ma_score = 30
    else:
        # Partial accumulation if above key averages
        if ltp > sma_20:
            ma_score += 10
        if ltp > sma_50:
            ma_score += 10
        if ltp > sma_200:
            ma_score += 10
        if golden_cross and ma_score < 30:
            ma_score = min(30, ma_score + 10)

    # 2. RSI (25 pts)
    if 45.0 <= rsi <= 60.0:
        rsi_score = 25
    elif rsi < 30.0:  # Oversold bounce
        rsi_score = 20
    elif 60.0 < rsi <= 70.0:
        rsi_score = 15
    elif 30.0 <= rsi < 45.0:
        rsi_score = 10
    else:  # > 70 or < 30 without bounce / extreme
        rsi_score = 0

    # 3. MACD (20 pts)
    if macd_line > signal_line and (macd_hist > 0 or hist_expanding):
        macd_score = 20
    elif macd_line > signal_line or abs(macd_line - signal_line) <= 0.05:
        macd_score = 10
    else:
        macd_score = 0

    # 4. Volume & Price Action (25 pts)
    if is_breakout or (vol_ratio >= 1.5 and is_green_day):
        vol_score = 25
    elif vol_ratio >= 1.0 and is_green_day:
        vol_score = 15
    elif vol_ratio >= 0.7:
        vol_score = 10
    else:
        vol_score = 5

    total_score = ma_score + rsi_score + macd_score + vol_score

    # 5. Signal Thresholds:
    # 80-100: STRONG BUY | 60-79: BUY | 40-59: HOLD | 20-39: SELL | 0-19: STRONG SELL
    if total_score >= 80:
        signal = "STRONG BUY"
    elif total_score >= 60:
        signal = "BUY"
    elif total_score >= 40:
        signal = "HOLD"
    elif total_score >= 20:
        signal = "SELL"
    else:
        signal = "STRONG SELL"

    return {
        "ma_score": ma_score,
        "rsi_score": rsi_score,
        "macd_score": macd_score,
        "vol_score": vol_score,
        "total_score": total_score,
        "signal": signal
    }


def generate_trade_report(ticker: str) -> str:
    """
    Executes the full automated workflow and returns the formatted Technical Trade Signal Report.
    """
    sym = ticker.strip().upper()
    df = fetch_ticker_data_stocknow(sym)
    
    if df is None or len(df) < 5:
        return f"Error: Unable to fetch technical indicator data for ticker '{sym}' from StockNow / DSE feeds."

    tech = calculate_technical_indicators(df)
    scores = compute_technical_score(tech)

    report = f"""-------------------------------------------------
Ticker: {sym} | Price: {tech['ltp']:.2f} | Signal: {scores['signal']} | Score: {scores['total_score']}/100
- Trend (MA): {scores['ma_score']}/30
- Momentum (RSI): {scores['rsi_score']}/25
- MACD: {scores['macd_score']}/20
- Volume: {scores['vol_score']}/25
Key Levels -> Entry: {tech['entry_price']:.2f} | Target: {tech['target_price']:.2f} | Stop Loss: {tech['stop_loss']:.2f}
-------------------------------------------------"""
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="StockNow Technical Trade Signal Automation Agent")
    parser.add_argument("ticker", nargs="?", default="SQURPHARMA", help="Target DSE Ticker Symbol (e.g. SQURPHARMA, GP, BATBC)")
    args = parser.parse_args()

    print(generate_trade_report(args.ticker))
