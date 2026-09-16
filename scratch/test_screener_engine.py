import pandas as pd, numpy as np

def test_screener_execution():
    dates = pd.date_range(end='2026-09-15', periods=60, freq='D')
    prices = 100.0 + np.cumsum(np.random.randn(60) * 0.5)
    highs = prices + 1.0
    lows = prices - 1.0
    opens = prices - 0.1
    closes = prices + 0.1
    volumes = np.full(60, 50000.0)

    # Make last bar a breakout
    highs[-1] = highs[-21:-1].max() + 1.5
    closes[-1] = highs[-1] - 0.2
    volumes[-1] = 100000.0

    df = pd.DataFrame({
        'open': opens, 'high': highs, 'low': lows, 'close': closes, 'volume': volumes
    }, index=dates)

    # Basic indicator checks
    vol_sma20 = float(df['volume'].rolling(20).mean().iloc[-1])
    vol_ratio = (float(df['volume'].iloc[-1]) / vol_sma20)
    high_20d = float(df['high'].iloc[-21:-1].max())
    is_p1 = (float(df['close'].iloc[-1]) >= high_20d) and (vol_ratio >= 1.5)

    print(f"P1 result: {is_p1} (Vol ratio: {vol_ratio:.2f}, 20D High: {high_20d:.2f}, Close: {df['close'].iloc[-1]:.2f})")

test_screener_execution()
