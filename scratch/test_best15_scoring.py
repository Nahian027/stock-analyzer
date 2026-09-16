import pandas as pd, numpy as np

def compute_composite_score(df: pd.DataFrame, ltp: float) -> dict:
    if df is None or len(df) < 25:
        return {"score": 0, "catalyst": "Insufficient Data"}

    close = df['close']
    high = df['high']
    low = df['low']
    volume = df['volume']

    # Indicators
    vol_sma20 = float(volume.rolling(20).mean().iloc[-1])
    cur_vol = float(volume.iloc[-1])
    vol_ratio = (cur_vol / vol_sma20) if vol_sma20 > 0 else 1.0

    ema20 = close.ewm(span=20, adjust=False).mean()
    ema50 = close.ewm(span=50, adjust=False).mean()
    ema200 = close.ewm(span=200, adjust=False).mean()
    sma20 = close.rolling(20).mean()
    sma20_std = close.rolling(20).std()
    bb_upper = sma20 + (2.0 * sma20_std)
    bb_lower = sma20 - (2.0 * sma20_std)
    bb_width = (bb_upper - bb_lower) / (sma20 + 1e-9)

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    macd_sig = macd.ewm(span=9, adjust=False).mean()
    macd_hist = macd - macd_sig

    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=10, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=10, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))

    # ATR
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = float(tr.ewm(alpha=1/14, min_periods=10, adjust=False).mean().iloc[-1])

    c_cur = float(close.iloc[-1])
    e20 = float(ema20.iloc[-1])
    e50 = float(ema50.iloc[-1])
    rsi_v = float(rsi.iloc[-1])
    m_line = float(macd.iloc[-1])
    m_sig = float(macd_sig.iloc[-1])
    m_h_cur = float(macd_hist.iloc[-1])
    m_h_prev = float(macd_hist.iloc[-2]) if len(macd_hist) >= 2 else m_h_cur
    cur_bbw = float(bb_width.iloc[-1])
    min_bbw_20 = float(bb_width.iloc[-20:].min()) if len(bb_width) >= 20 else cur_bbw

    catalyst_tags = []

    # 1. Volume & Liquidity Surge (30 pts)
    # Current Day Volume >= 2.0x SMA20 = 30 pts; linear scaling down to 10 pts for 1.2x
    vol_pts = 0.0
    if vol_ratio >= 2.0:
        vol_pts = 30.0
        catalyst_tags.append(f"Volume Surge ({vol_ratio:.1f}x SMA20)")
    elif vol_ratio >= 1.2:
        vol_pts = 10.0 + ((vol_ratio - 1.2) / 0.8) * 20.0
        catalyst_tags.append(f"Volume Expansion ({vol_ratio:.1f}x)")
    elif vol_ratio >= 1.0:
        vol_pts = 5.0
    else:
        vol_pts = 0.0

    # 2. Trend & Moving Average Alignment (30 pts)
    # Price > 20 EMA > 50 EMA = 20 pts
    # Golden Cross or Price crossing above 20 EMA today = +10 pts
    trend_pts = 0.0
    if c_cur > e20 > e50:
        trend_pts += 20.0
        catalyst_tags.append("Price > 20 EMA > 50 EMA")
    elif c_cur > e20:
        trend_pts += 10.0

    # Golden cross or crossing above 20 EMA today
    crossed_ema20_today = (c_cur >= e20) and (float(close.iloc[-2]) < float(ema20.iloc[-2]) if len(close) >= 2 else False)
    golden_cross = (e20 > e50) and (float(ema20.iloc[-2]) <= float(ema50.iloc[-2]) if len(ema20) >= 2 else False)
    if crossed_ema20_today:
        trend_pts += 10.0
        catalyst_tags.append("Price Crossed Above 20 EMA")
    elif golden_cross:
        trend_pts += 10.0
        catalyst_tags.append("EMA 20/50 Golden Cross")
    elif c_cur > e20 and c_cur > float(ema200.iloc[-1]):
        trend_pts += 5.0

    trend_pts = min(30.0, trend_pts)

    # 3. Momentum & Strength (25 pts)
    # RSI between 52 and 68 = 15 pts
    # MACD Line > Signal Line with rising positive histogram = 10 pts
    mom_pts = 0.0
    if 52.0 <= rsi_v <= 68.0:
        mom_pts += 15.0
        catalyst_tags.append(f"RSI Momentum ({rsi_v:.1f})")
    elif 48.0 <= rsi_v <= 72.0:
        mom_pts += 8.0

    if (m_line > m_sig) and (m_h_cur > 0) and (m_h_cur >= m_h_prev):
        mom_pts += 10.0
        catalyst_tags.append("MACD Bullish Histogram Expansion")
    elif m_line > m_sig:
        mom_pts += 5.0

    mom_pts = min(25.0, mom_pts)

    # 4. Volatility Compression (15 pts)
    # Bollinger Band width near 20-day minimum prior to expansion = 15 pts
    volat_pts = 0.0
    if cur_bbw <= min_bbw_20 * 1.25:
        volat_pts = 15.0
        catalyst_tags.append("Bollinger Squeeze Compression")
    elif cur_bbw <= min_bbw_20 * 1.50:
        volat_pts = 10.0
        catalyst_tags.append("Volat Compression")
    else:
        volat_pts = 5.0

    total_score = round(vol_pts + trend_pts + mom_pts + volat_pts, 1)

    # Buy zone & stop loss
    buy_low = round(min(ltp * 0.99, max(0.1, e20 * 0.995)), 2)
    buy_high = round(ltp * 1.005, 2)
    stop_loss = round(max(0.1, ltp - (1.5 * atr)), 2)

    primary_catalyst = " + ".join(catalyst_tags[:3]) if catalyst_tags else "Technical Baseline Alignment"

    return {
        "score": total_score,
        "vol_pts": round(vol_pts, 1),
        "trend_pts": round(trend_pts, 1),
        "mom_pts": round(mom_pts, 1),
        "volat_pts": round(volat_pts, 1),
        "catalyst": primary_catalyst,
        "buy_zone": f"Tk {buy_low:.2f} – {buy_high:.2f}",
        "stop_loss": stop_loss,
        "rsi": rsi_v,
        "vol_ratio": vol_ratio,
        "atr": atr
    }

print("Scoring model verified successfully.")
