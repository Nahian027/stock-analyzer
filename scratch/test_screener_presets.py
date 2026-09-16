import pandas as pd, numpy as np, datetime as dt

def run_screener_test():
    # Synthetic OHLCV
    dates = pd.date_range(end=dt.datetime.now(), periods=65, freq='D')
    prices = 100.0 + np.cumsum(np.random.randn(65) * 0.8)
    highs = prices + np.random.uniform(0.5, 1.5, 65)
    lows = prices - np.random.uniform(0.5, 1.5, 65)
    opens = (highs + lows) / 2.0
    closes = prices
    volumes = np.full(65, 100000.0)

    # 1. Preset 1: Breakout setup
    highs[-1] = highs[-21:-1].max() + 2.0
    closes[-1] = highs[-1] - 0.2
    volumes[-1] = 200000.0 # 2.0x volume

    df = pd.DataFrame({'open': opens, 'high': highs, 'low': lows, 'close': closes, 'volume': volumes}, index=dates)

    # Indicator calculation
    close = df['close']
    high = df['high']
    low = df['low']
    vol = df['volume']

    # 20-day High (lookback prior 20 bars)
    high_20d_prev = float(high.iloc[-21:-1].max()) if len(high) >= 21 else float(high.max())
    c_cur = float(close.iloc[-1])
    is_breakout_20d = c_cur >= high_20d_prev

    # Volume SMA20
    vol_sma20 = float(vol.rolling(20).mean().iloc[-1])
    vol_cur = float(vol.iloc[-1])
    vol_ratio = (vol_cur / vol_sma20) if vol_sma20 > 0 else 1.0

    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=10, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=10, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    rsi_cur = float(rsi.iloc[-1])

    # Keltner & Bollinger
    sma20 = close.rolling(20).mean()
    sma20_std = close.rolling(20).std()
    bb_upper = sma20 + (2.0 * sma20_std)
    bb_lower = sma20 - (2.0 * sma20_std)
    bb_width = (bb_upper - bb_lower) / (sma20 + 1e-9)

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr14 = tr.ewm(alpha=1/14, min_periods=10, adjust=False).mean()
    ema20 = close.ewm(span=20, adjust=False).mean()
    kc_upper = ema20 + (1.5 * atr14)
    kc_lower = ema20 - (1.5 * atr14)

    cur_bb_up = float(bb_upper.iloc[-1])
    cur_bb_lo = float(bb_lower.iloc[-1])
    cur_kc_up = float(kc_upper.iloc[-1])
    cur_kc_lo = float(kc_lower.iloc[-1])
    cur_bbw = float(bb_width.iloc[-1])
    min_bbw_20 = float(bb_width.iloc[-20:].min())

    bb_inside_kc = (cur_bb_up <= cur_kc_up) and (cur_bb_lo >= cur_kc_lo)
    bb_squeeze = bb_inside_kc or (cur_bbw <= min_bbw_20 * 1.25)

    # 3-session volume contraction
    vol_declining_3d = (vol.iloc[-1] < vol.iloc[-2] < vol.iloc[-3]) if len(vol) >= 3 else False

    print("Preset 1 Check:")
    print(f"20D High: {high_20d_prev:.2f} | Close: {c_cur:.2f} | Breakout: {is_breakout_20d}")
    print(f"Vol Ratio: {vol_ratio:.2f} (>= 1.5x: {vol_ratio >= 1.5})")
    print(f"RSI: {rsi_cur:.2f} (55-75: {55 < rsi_cur < 75})")
    print(f"Preset 1 Pass: {is_breakout_20d and (vol_ratio >= 1.5) and (55 < rsi_cur < 75)}")

    print("\nPreset 3 Squeeze Check:")
    print(f"BB Squeeze: {bb_squeeze} | Vol 3D Declining: {vol_declining_3d}")

run_screener_test()
