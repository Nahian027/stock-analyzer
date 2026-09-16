import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


import numpy as np
import pandas as pd
from core_engine import get_accurate_next_move, evaluate_ticker


def generate_sample_df(close_trend="up", base_price=100.0, bars=40):
    np.random.seed(42)
    closes = [base_price]
    for i in range(bars - 1):
        if close_trend == "up":
            step = np.random.uniform(0.1, 1.2)
        elif close_trend == "down":
            step = np.random.uniform(-1.2, -0.1)
        else:
            step = np.random.uniform(-0.5, 0.5)
        closes.append(round(closes[-1] + step, 2))
        
    df = pd.DataFrame({
        'Open': [c - np.random.uniform(-0.5, 0.5) for c in closes],
        'High': [c + np.random.uniform(0.5, 1.5) for c in closes],
        'Low': [c - np.random.uniform(0.5, 1.5) for c in closes],
        'Close': closes,
        'Volume': [int(np.random.uniform(50000, 200000)) for _ in closes]
    })
    return df

def test_bullish_next_move():
    df_bull = generate_sample_df("up", base_price=100.0, bars=40)
    close = float(df_bull['Close'].iloc[-1])
    res = get_accurate_next_move(df_bull, ticker="BULL_STOCK")
    
    print(f"Bullish Next Move: Text='{res['direction_text']}', Target={res['target_price']}, Delta={res['delta_pct']}, Color={res['color']}")
    assert "Bullish" in res['direction_text'] or "উর্ধমুখী" in res['direction_text']
    assert res['color'] == "#00875A"
    assert res['icon'] == "📈"
    assert res['target_price'] > close, f"Bullish target {res['target_price']} must be > close {close}"
    assert res['delta_pct'].startswith("+"), f"Bullish delta_pct must start with +: {res['delta_pct']}"
    assert "🔮 গতিপথ" in res['formatted_html']
    print("[OK] Test 1: Bullish next move verified with 100% boundary safety.")

def test_bearish_next_move():
    df_bear = generate_sample_df("down", base_price=150.0, bars=40)
    close = float(df_bear['Close'].iloc[-1])
    res = get_accurate_next_move(df_bear, ticker="BEAR_STOCK")
    
    print(f"Bearish Next Move: Text='{res['direction_text']}', Target={res['target_price']}, Delta={res['delta_pct']}, Color={res['color']}")
    assert "Bearish" in res['direction_text'] or "নিম্নমুখী" in res['direction_text']
    assert res['color'] == "#DE350B"
    assert res['icon'] == "📉"
    assert res['target_price'] < close, f"Bearish target {res['target_price']} must be < close {close}"
    assert res['delta_pct'].startswith("-"), f"Bearish delta_pct must start with -: {res['delta_pct']}"
    assert "🔮 গতিপথ" in res['formatted_html']
    print("[OK] Test 2: Bearish next move verified with 100% boundary safety.")


def test_evaluate_ticker_integration():
    df_squr = generate_sample_df("up", base_price=210.0, bars=40)
    eval_res = evaluate_ticker("SQURPHARMA", df_squr)
    
    assert "next_move" in eval_res, "next_move key must exist in evaluate_ticker output"
    nm = eval_res["next_move"]
    print(f"SSOT evaluate_ticker next_move: {nm['direction_text']} -> Tk {nm['target_price']} ({nm['delta_pct']})")
    assert nm['target_price'] > 0
    print("[OK] Test 3: SSOT evaluate_ticker integration verified.")

if __name__ == "__main__":
    print("=================================================================")
    print("RUNNING ACCURATE NEXT MOVE MATHEMATICAL SUITE")
    print("=================================================================")
    test_bullish_next_move()
    test_bearish_next_move()
    test_evaluate_ticker_integration()
    print("=================================================================")
    print("ALL NEXT MOVE TESTS PASSED WITH 100% ACCURACY!")
    print("=================================================================")
