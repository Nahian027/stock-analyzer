import sys, os, datetime as dt
import pandas as pd, numpy as np

# Mock or test the new forecasting logic
def test_volatility_forecasting():
    dates = pd.date_range(end=dt.datetime.now(), periods=65, freq='D')
    prices = 100.0 + np.cumsum(np.random.randn(65) * 0.8)
    highs = prices + np.random.uniform(0.5, 1.5, 65)
    lows = prices - np.random.uniform(0.5, 1.5, 65)
    opens = (highs + lows) / 2.0
    closes = prices
    volumes = np.full(65, 150000.0)

    df = pd.DataFrame({
        'open': opens, 'high': highs, 'low': lows, 'close': closes, 'volume': volumes
    }, index=dates)

    # Compute indicators
    close = df['close']
    high = df['high']
    low = df['low']

    # ATR 14
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['ATR'] = tr.ewm(alpha=1/14, min_periods=10, adjust=False).mean()

    # EMA 20
    df['EMA_20'] = close.ewm(span=20, adjust=False).mean()

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=10, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=10, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    ltp = float(df['close'].iloc[-1])
    atr = float(df['ATR'].iloc[-1])
    
    # 1. 20 EMA Slope
    ema20_s = df['EMA_20']
    ema20_slope = (float(ema20_s.iloc[-1]) - float(ema20_s.iloc[-4])) / (3.0 * atr + 1e-9)
    ema20_norm = float(np.tanh(ema20_slope * 2.5))

    # 2. MACD Histogram Velocity
    macd_h = df['MACD_Hist']
    macd_velocity = (float(macd_h.iloc[-1]) - float(macd_h.iloc[-3])) / (2.0 * atr + 1e-9)
    macd_norm = float(np.tanh(macd_velocity * 3.0))

    # 3. 14-period RSI Divergence / Momentum
    rsi_cur = float(df['RSI'].iloc[-1])
    rsi_mom = (rsi_cur - 50.0) / 25.0
    rsi_norm = float(np.clip(rsi_mom, -1.0, 1.0))

    # Composite alignment score (-1.0 to +1.0)
    composite_z = float(np.clip(0.35 * ema20_norm + 0.35 * macd_norm + 0.30 * rsi_norm, -1.0, 1.0))
    probability_score = round(min(98.0, max(50.0, 50.0 + (abs(composite_z) * 45.0))), 1)

    if composite_z >= 0.15:
        directional_bias = "Bullish"
    elif composite_z <= -0.15:
        directional_bias = "Bearish"
    else:
        directional_bias = "Neutral"

    # Expected 5-Day Range (Close +/- 2 * ATR)
    range_upper = round(ltp + (2.0 * atr), 2)
    range_lower = round(max(0.1, ltp - (2.0 * atr)), 2)

    # Bullish / Bearish Targets & Invalidation Levels
    bullish_target = round(ltp + (1.5 * atr), 2)
    bearish_target = round(max(0.1, ltp - (1.5 * atr)), 2)
    invalidation_level = round(max(0.1, ltp - (1.0 * atr)), 2) if directional_bias == "Bullish" else round(ltp + (1.0 * atr), 2)

    # Support / Resistance 30-Day Pivot Boundaries
    pivot_r30 = round(float(df['high'].iloc[-30:].max()), 2)
    pivot_s30 = round(float(df['low'].iloc[-30:].min()), 2)

    # Constrained target
    if directional_bias == "Bullish":
        expected_target = round(min(pivot_r30, bullish_target), 2)
    elif directional_bias == "Bearish":
        expected_target = round(max(pivot_s30, bearish_target), 2)
    else:
        expected_target = round(min(pivot_r30, max(pivot_s30, ltp + composite_z * 1.5 * atr)), 2)

    rr_ratio = 1.50

    print("=== Volatility Forecasting Results ===")
    print(f"LTP: Tk {ltp:.2f} | ATR(14): Tk {atr:.2f}")
    print(f"EMA20 Slope: {ema20_slope:.4f} (Norm: {ema20_norm:.2f})")
    print(f"MACD Velocity: {macd_velocity:.4f} (Norm: {macd_norm:.2f})")
    print(f"RSI: {rsi_cur:.1f} (Norm: {rsi_norm:.2f})")
    print(f"Composite Z: {composite_z:.2f} => Directional Bias: {directional_bias} ({probability_score}% Prob)")
    print(f"Expected 5-Day Range: Tk {range_lower:.2f} - {range_upper:.2f}")
    print(f"5-Day Expected Target: Tk {expected_target:.2f} | Invalidation Stop: Tk {invalidation_level:.2f} | R:R: 1:{rr_ratio:.2f}")
    print(f"30-Day Pivot Resistance (R30): Tk {pivot_r30:.2f} | Pivot Support (S30): Tk {pivot_s30:.2f}")

test_volatility_forecasting()
