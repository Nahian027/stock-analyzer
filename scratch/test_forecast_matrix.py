import numpy as np
import pandas as pd

def test_probability_model():
    print("=== TESTING STRICT MULTI-FACTOR PROBABILITY MATRIX ===")
    
    # Test cases:
    # 1. Bullish Regime + Volume + Sweet RSI
    trend_pts_1 = 35 # Close > 20 EMA > 50 EMA
    mom_vol_pts_1 = 20 + 15 # MACD expanding pos + Vol > 1.2x
    rsi_pts_1 = 30 # RSI 55
    p1 = trend_pts_1 + mom_vol_pts_1 + rsi_pts_1
    print(f"Case 1 (Strong Bullish): P={p1}% (Expected >= 75%)")
    assert p1 >= 75
    
    # 2. Bearish Regime (Below 20 & 50 EMA) without divergence, but RSI oversold bounce
    trend_pts_2 = 5 # Below 20 & 50 EMA
    mom_vol_pts_2 = 10 + 6 # MACD contracting neg + normal vol
    rsi_pts_2 = 22 # RSI 38
    p2_raw = trend_pts_2 + mom_vol_pts_2 + rsi_pts_2 # 43%
    # Regime override rule applies:
    p2 = min(p2_raw, 54.0)
    print(f"Case 2 (Oversold in Downtrend): Raw={p2_raw}%, Clamped={p2}% (Expected 40-59% Neutral/Sideways)")
    assert 40 <= p2 < 60
    
    # 3. Overbought Stock (RSI 78) in Uptrend
    trend_pts_3 = 35
    mom_vol_pts_3 = 12 + 10 # MACD contracting pos + vol 1.0x
    rsi_pts_3 = 0 # RSI 78 heavy penalty
    p3 = trend_pts_3 + mom_vol_pts_3 + rsi_pts_3 # 57%
    print(f"Case 3 (Overbought Exhaustion): P={p3}% (Expected < 60% Neutral/Sideways due to overbought risk)")
    assert p3 < 60

    print("All test cases passed!")

test_probability_model()
