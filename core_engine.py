"""
Core Single Source of Truth (SSOT) Continuous Scoring & Technical Analysis Engine.
Implements Continuous Normalized Composite Scoring (0-100), Dynamic Volatility RRR,
and Rational Signal Thresholds.
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Any


def calculate_rsi(series: pd.Series, period: int = 14) -> float:
    """
    Standard Wilder's / Exponential RSI calculation on Close prices.
    Returns float value between 0.0 and 100.0.
    """
    if series is None or len(series) < 2:
        return 50.0

    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period, min_periods=min(3, len(series))).mean()
    avg_loss = loss.rolling(window=period, min_periods=min(3, len(series))).mean()

    # Wilder's smoothing if sufficient data
    if len(series) > period:
        for i in range(period, len(series)):
            avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (period - 1) + gain.iloc[i]) / period
            avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (period - 1) + loss.iloc[i]) / period

    last_gain = float(avg_gain.iloc[-1]) if pd.notnull(avg_gain.iloc[-1]) else 0.0
    last_loss = float(avg_loss.iloc[-1]) if pd.notnull(avg_loss.iloc[-1]) else 0.0

    if last_loss == 0.0:
        return 100.0 if last_gain > 0 else 50.0
    
    rs = last_gain / last_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return float(np.clip(rsi, 0.0, 100.0))


def get_accurate_next_move(df_daily: pd.DataFrame, ticker: str = "") -> Dict[str, Any]:
    """
    Directional Vector Determination & Accurate Directional Bias.
    Grounded 100% in trend (20 EMA), ATR(14) volatility, RSI(14) momentum, and structural pivots.
    """
    if df_daily is None or len(df_daily) < 2:
        return {
            "direction_text": "কনসলিডেশন (Range)",
            "icon": "⚖️",
            "color": "#0284c7",
            "target_price": 0.0,
            "delta_pct": "+0.0%",
            "formatted_html": """<div style="display: flex; justify-content: space-between; align-items: center; font-size: 13.5px; font-weight: 600;">
  <span style="color: #4A5568;">🔮 গতিপথ (Directional Bias):</span>
  <span style="color: #0284c7;">
    ⚖️ কনসলিডেশন (Range)
  </span>
</div>"""
        }

    # Normalize column casing
    col_map = {c: c.capitalize() for c in df_daily.columns}
    df = df_daily.rename(columns=col_map).copy()
    
    close = float(df['Close'].iloc[-1])
    ema_20 = float(df['Close'].ewm(span=20, adjust=False).mean().iloc[-1])
    
    # 1. ATR(14) calculation
    tr = pd.concat([
        df['High'] - df['Low'],
        (df['High'] - df['Close'].shift(1)).abs(),
        (df['Low'] - df['Close'].shift(1)).abs()
    ], axis=1).max(axis=1)
    atr_14 = float(tr.rolling(14, min_periods=min(3, len(df))).mean().iloc[-1])
    if pd.isna(atr_14) or atr_14 <= 0:
        atr_14 = max(0.5, close * 0.02)
    
    # 2. RSI(14)
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14, min_periods=min(3, len(df))).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14, min_periods=min(3, len(df))).mean()
    rs = gain / (loss + 1e-9)
    rsi_14 = float((100 - (100 / (1 + rs))).iloc[-1])
    if pd.isna(rsi_14):
        rsi_14 = 50.0
    
    # 3. Direction Decision Rules:
    # Bullish bias: Price above 20 EMA, or RSI bouncing from oversold (<35) with green candle
    prev_close = float(df['Close'].iloc[-2]) if len(df) >= 2 else close
    pct_day = (close - prev_close) / (prev_close + 1e-9)
    
    is_bullish = (close >= ema_20 and rsi_14 >= 45) or (rsi_14 < 35 and pct_day > 0)
    is_bearish = (close < ema_20 and rsi_14 < 45) or (rsi_14 > 72 and pct_day < 0)
    
    # ---------------------------------------------------------
    # 4. Target Calculation based on Direction
    # ---------------------------------------------------------
    tail_highs = df['High'].tail(min(30, len(df)))
    overhead_pivots = tail_highs[tail_highs > close * 1.008]
    if not overhead_pivots.empty:
        res_target = min(float(overhead_pivots.min()), close + (2.0 * atr_14))
        res_target = max(res_target, close + (1.25 * atr_14))
    else:
        res_target = close + (1.75 * atr_14)
    res_target = round(max(res_target, close * 1.015), 2)

    tail_lows = df['Low'].tail(min(30, len(df)))
    downside_pivots = tail_lows[tail_lows < close * 0.992]
    if not downside_pivots.empty:
        sup_target = max(float(downside_pivots.max()), close - (2.0 * atr_14))
        sup_target = min(sup_target, close - (1.0 * atr_14))
    else:
        sup_target = close - (1.5 * atr_14)
    sup_target = round(min(sup_target, close * 0.985), 2)

    if is_bullish:
        direction_text = "উর্ধমুখী (Bullish)"
        icon = "📈"
        color = "#00875A"  # Institutional Green
        target_price = res_target
        delta_pts = round(target_price - close, 2)
        delta_pct_num = round((delta_pts / (close + 1e-9)) * 100, 2)
        delta_pct_str = f"+{abs(delta_pct_num):.1f}%"
        
    elif is_bearish:
        direction_text = "নিম্নমুখী (Bearish)"
        icon = "📉"
        color = "#DE350B"  # Institutional Red
        target_price = sup_target
        delta_pts = round(target_price - close, 2)
        delta_pct_num = round((delta_pts / (close + 1e-9)) * 100, 2)
        delta_pct_str = f"-{abs(delta_pct_num):.1f}%"
        
    else:
        direction_text = "কনসলিডেশন (Range)"
        icon = "⚖️"
        color = "#0284c7"  # Deep Blue
        target_price = res_target
        delta_pts = round(target_price - close, 2)
        delta_pct_num = round((delta_pts / (close + 1e-9)) * 100, 2)
        delta_pct_str = f"+{abs(delta_pct_num):.1f}%"
        
    formatted_html = f"""<div style="display: flex; justify-content: space-between; align-items: center; font-size: 13.5px; font-weight: 600;">
  <span style="color: #4A5568;">🔮 গতিপথ (Directional Bias):</span>
  <span style="color: {color};">
    {icon} {direction_text}
  </span>
</div>"""

    return {
        "direction_text": direction_text,
        "icon": icon,
        "color": color,
        "target_price": target_price,
        "delta_pct": delta_pct_str,
        "formatted_html": formatted_html
    }



def calculate_composite_score(df_daily: pd.DataFrame, df_5m: Optional[pd.DataFrame] = None, rsi_5m_val: float = 50.0, detected_pattern: str = "No Distinct Pattern") -> int:
    """
    Continuous Institutional Scoring Model (0 - 100).
    Rewards both Trend Following and Oversold/Candlestick Reversal Accumulation setups.
    """
    if df_daily is None or len(df_daily) < 2:

        return 50

    col_map = {c: c.capitalize() for c in df_daily.columns}
    df = df_daily.rename(columns=col_map).copy()

    close = float(df['Close'].iloc[-1])
    prev_close = float(df['Close'].iloc[-2]) if len(df) >= 2 else close
    pct_change = float(((close - prev_close) / (prev_close + 1e-9)) * 100)
    score = 0.0

    # 1. Trend & Moving Average Alignment (Max 30 pts)
    ema_20_series = df['Close'].ewm(span=20, adjust=False).mean()
    ema_20 = float(ema_20_series.iloc[-1]) if pd.notnull(ema_20_series.iloc[-1]) else close
    sma_50_series = df['Close'].rolling(50, min_periods=min(10, len(df))).mean()
    sma_50 = float(sma_50_series.iloc[-1]) if pd.notnull(sma_50_series.iloc[-1]) else ema_20

    dist_ema20 = (close - ema_20) / (ema_20 + 1e-9)
    if close >= ema_20:
        score += 20.0
    elif dist_ema20 >= -0.02:  # Within 2% of 20 EMA (testing dynamic support)
        score += 15.0
    elif dist_ema20 >= -0.04:
        score += 8.0

    if ema_20 >= sma_50:
        score += 10.0
    elif (ema_20 - sma_50) / (sma_50 + 1e-9) >= -0.02:
        score += 5.0

    # 2. RSI & Momentum Dynamics (Max 25 pts)
    rsi = calculate_rsi(df['Close'], period=14)
    if 45.0 <= rsi <= 65.0:
        score += 25.0
    elif rsi < 35.0:
        if pct_change > 0:
            score += 22.0  # Prime bottom rebound from oversold!
        else:
            score += 12.0  # Deep oversold watch
    elif 65.0 < rsi <= 75.0:
        score += 18.0
    elif 35.0 <= rsi < 45.0:
        score += 15.0

    # 3. Volume & Liquidity Expansion (Max 20 pts)
    vol_ratio = 1.0
    if 'Volume' in df.columns:
        vol_ma = float(df['Volume'].rolling(20, min_periods=min(3, len(df))).mean().iloc[-1])
        vol_ratio = float(df['Volume'].iloc[-1] / (vol_ma + 1e-9)) if vol_ma > 0 else 1.0

    if vol_ratio >= 1.5:
        score += 20.0
    elif vol_ratio >= 1.0:
        score += 15.0
    elif vol_ratio >= 0.7:
        score += 10.0
    else:
        score += 5.0

    # 4. Day Price Action & Candlestick Catalyst (Max 25 pts)
    if pct_change > 0:
        score += min(10.0, 4.0 + (pct_change * 2.0))
    elif pct_change == 0:
        score += 4.0

    if detected_pattern in ["Bullish Engulfing", "Hammer", "Morning Star", "Double Bottom"]:
        score += 15.0
    elif detected_pattern in ["Inverted Hammer", "Doji Reversal", "Piercing Line"]:
        score += 10.0
    elif detected_pattern == "Bearish Engulfing":
        score -= 10.0

    return int(round(min(100.0, max(0.0, score)), 0))



def evaluate_ticker(ticker: str, df_daily: pd.DataFrame, df_5m: Optional[pd.DataFrame] = None, rsi_5m_val: float = 50.0) -> Dict[str, Any]:
    """
    Single unified evaluation engine for any ticker.
    Guarantees Single Source of Truth across Card and Table views.
    
    Parameters:
        ticker: Stock symbol string (e.g. 'SQURPHARMA')
        df_daily: DataFrame containing daily OHLCV bars (minimum 10 bars recommended)
        df_5m: Optional DataFrame with intraday 5-minute bars
        rsi_5m_val: Optional pre-computed 5M RSI float
        
    Returns:
        Unified dictionary with all technical metrics, continuous score, pattern, signal, and setup_status.
    """
    if df_daily is None or len(df_daily) < 2:
        close_fallback = 0.0
        return {
            "ticker": ticker,
            "symbol": ticker,
            "close": close_fallback,
            "prev_close": close_fallback,
            "pct_change": 0.0,
            "pattern": "No Distinct Pattern",
            "pattern_bias": "Neutral",
            "score": 50,
            "signal": "HOLD",
            "setup_status": "Consolidating / Range",
            "target": close_fallback,
            "target_pct": 0.0,
            "floor": close_fallback,
            "floor_pct": 0.0,
            "rrr": 1.5,
            "rsi_1d": 50.0,
            "rsi_5m": round(rsi_5m_val, 1),
            "atr": 0.0,
            "ema_20": 0.0,
            "vol_ratio": 1.0
        }

    # Normalize column casing
    col_map = {c: c.capitalize() for c in df_daily.columns}
    df = df_daily.rename(columns=col_map).copy()

    # 1. Price metrics
    close = round(float(df['Close'].iloc[-1]), 2)
    prev_close = round(float(df['Close'].iloc[-2]), 2)
    pct_change = round(((close - prev_close) / (prev_close + 1e-9)) * 100, 2)
    
    open_p = float(df['Open'].iloc[-1]) if 'Open' in df.columns else close
    high = float(df['High'].iloc[-1]) if 'High' in df.columns else close
    low = float(df['Low'].iloc[-1]) if 'Low' in df.columns else close

    prev_open = float(df['Open'].iloc[-2]) if len(df) >= 2 and 'Open' in df.columns else open_p

    # 2. Candlestick Pattern Engine (Strict, Single Definition)
    body = abs(close - open_p)
    total_range = high - low if high != low else 1e-5
    upper_wick = high - max(open_p, close)
    lower_wick = min(open_p, close) - low
    
    pattern = "No Distinct Pattern"
    pattern_bias = "Neutral"

    # Inverted Hammer: upper shadow >= 2x body and minimal lower shadow
    if upper_wick >= 2.0 * body and lower_wick <= 0.15 * total_range and total_range > 0:
        pattern = "Inverted Hammer"
        pattern_bias = "Bullish"
    # Hammer: lower shadow >= 2x body and minimal upper shadow
    elif lower_wick >= 2.0 * body and upper_wick <= 0.15 * total_range and total_range > 0:
        pattern = "Hammer"
        pattern_bias = "Bullish"
    # Bullish Engulfing
    elif (prev_close < prev_open) and (close > open_p) and (close >= prev_open) and (open_p <= prev_close):
        pattern = "Bullish Engulfing"
        pattern_bias = "Bullish"
    # Bearish Engulfing
    elif (prev_close > prev_open) and (close < open_p) and (close <= prev_open) and (open_p >= prev_close):
        pattern = "Bearish Engulfing"
        pattern_bias = "Bearish"
    # Double Bottom (W-Pattern) in recent 25 bars
    else:
        recent_lows = df['Low'].tail(min(25, len(df))).values
        if len(recent_lows) >= 15:
            split_idx = len(recent_lows) // 2
            min_idx1 = np.argmin(recent_lows[:split_idx])
            min_idx2 = split_idx + np.argmin(recent_lows[split_idx:])
            l1, l2 = recent_lows[min_idx1], recent_lows[min_idx2]
            if abs(l1 - l2) / (l1 + 1e-9) <= 0.015 and close > max(l1, l2) * 1.02:
                pattern = "Double Bottom"
                pattern_bias = "Bullish"

    # 3. Dynamic Volatility ATR & Support / Resistance Room (Non-Static RRR)
    tr = pd.concat([
        df['High'] - df['Low'],
        (df['High'] - df['Close'].shift(1)).abs(),
        (df['Low'] - df['Close'].shift(1)).abs()
    ], axis=1).max(axis=1)
    
    atr_series = tr.rolling(14, min_periods=min(3, len(df))).mean()
    atr = float(atr_series.iloc[-1]) if pd.notnull(atr_series.iloc[-1]) else (close * 0.025)
    if atr <= 0:
        atr = max(0.5, close * 0.02)
    
    # Calculate real structural resistance and support from historical swing peaks/troughs (60 bars)
    high_series = df['High'].tail(min(60, len(df)))
    low_series = df['Low'].tail(min(60, len(df)))
    
    # 1. Structural Resistance: Real swing highs strictly above current close (>= 1.0% above)
    real_overhead_highs = [float(h) for h in high_series.values if float(h) >= close * 1.01]
    if real_overhead_highs:
        nearest_resistance = min(real_overhead_highs)
        # If nearest high is too tight, pick secondary structural resistance
        if nearest_resistance < close * 1.015 and len(real_overhead_highs) > 1:
            higher_pivots = [h for h in real_overhead_highs if h >= close * 1.02]
            if higher_pivots:
                nearest_resistance = min(higher_pivots)
    else:
        # 52-week / multi-month breakout: dynamic upside target
        high_20 = float(high_series.tail(min(20, len(df))).max())
        nearest_resistance = max(high_20 * 1.035, close + (1.5 * atr))

    # 2. Structural Support Floor: Real swing lows strictly below current close (<= 1.0% below)
    real_downside_lows = [float(l) for l in low_series.values if float(l) <= close * 0.99]
    if real_downside_lows:
        nearest_support = max(real_downside_lows)
        # If nearest low is too tight, pick secondary structural support floor
        if nearest_support > close * 0.985 and len(real_downside_lows) > 1:
            lower_pivots = [l for l in real_downside_lows if l <= close * 0.98]
            if lower_pivots:
                nearest_support = max(lower_pivots)
    else:
        ema_20_series = df['Close'].ewm(span=20, adjust=False).mean()
        ema_20_val = float(ema_20_series.iloc[-1]) if pd.notnull(ema_20_series.iloc[-1]) else close * 0.98
        nearest_support = min(ema_20_val, close - (1.0 * atr))

    target = round(nearest_resistance, 2)
    floor = round(nearest_support, 2)

    # Safety bounds (guarantee floor < close < target with healthy margin)
    if floor >= close:
        floor = round(close * 0.965, 2)
    if target <= close:
        target = round(close * 1.045, 2)

    target_pct = round(((target - close) / (close + 1e-9)) * 100, 2)
    floor_pct = round(((floor - close) / (close + 1e-9)) * 100, 2)
    
    risk = max(0.05, close - floor)
    reward = max(0.05, target - close)
    dynamic_rrr = round(reward / risk, 2)


    # 4. Continuous Normalized Composite Score (0 - 100)
    score = calculate_composite_score(
        df_daily=df,
        df_5m=df_5m,
        rsi_5m_val=rsi_5m_val,
        detected_pattern=pattern
    )

    # 5. Strict Quantitative Signal Thresholds
    # 75 - 100: STRONG BUY
    # 55 - 74:  BUY
    # 40 - 54:  HOLD
    # 20 - 39:  SELL
    # 0  - 19:  STRONG SELL
    if score >= 75:
        signal = "STRONG BUY"
        setup_status = "Bullish Breakout"
    elif score >= 55:
        signal = "BUY"
        setup_status = "Bullish Setup"
    elif score >= 40:
        signal = "HOLD"
        setup_status = "Consolidating / Range"
    elif score >= 20:
        signal = "SELL"
        setup_status = "Bearish Breakdown"
    else:
        signal = "STRONG SELL"
        setup_status = "Severe Breakdown"


    rsi_1d = calculate_rsi(df['Close'], period=14)
    ema_20_val = float(df['Close'].ewm(span=20, adjust=False).mean().iloc[-1])
    
    vol_ratio = 1.0
    if 'Volume' in df.columns:
        vol_ma_val = float(df['Volume'].rolling(20, min_periods=min(3, len(df))).mean().iloc[-1])
        vol_ratio = float(df['Volume'].iloc[-1] / (vol_ma_val + 1e-9)) if vol_ma_val > 0 else 1.0

    next_move = get_accurate_next_move(df_daily=df, ticker=ticker)

    return {
        "ticker": ticker,
        "symbol": ticker,
        "close": close,
        "prev_close": prev_close,
        "pct_change": pct_change,
        "pattern": pattern,
        "pattern_bias": pattern_bias,
        "score": score,
        "signal": signal,
        "setup_status": setup_status,
        "target": target,
        "target_pct": target_pct,
        "floor": floor,
        "floor_pct": floor_pct,
        "rrr": dynamic_rrr,
        "rsi_1d": round(rsi_1d, 1),
        "rsi_5m": round(rsi_5m_val, 1),
        "atr": round(atr, 2),
        "ema_20": round(ema_20_val, 2),
        "vol_ratio": round(vol_ratio, 2),
        "next_move": next_move
    }

