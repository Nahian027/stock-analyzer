import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import pandas as pd
import numpy as np
from stocknow_agent import (
    calculate_technical_indicators,
    compute_technical_score,
    generate_trade_report,
    fetch_ticker_data_stocknow
)

def test_scoring_matrix():
    # 1. Strong Bullish Mock Tech Data
    bull_tech = {
        "ltp": 120.0,
        "sma_20": 110.0,
        "sma_50": 105.0,
        "sma_200": 100.0,
        "golden_cross": True,
        "rsi_14": 52.0,
        "macd_line": 2.5,
        "signal_line": 1.2,
        "macd_hist": 1.3,
        "hist_expanding": True,
        "vol_ratio": 1.8,
        "is_green_day": True,
        "is_breakout": True
    }
    score_res = compute_technical_score(bull_tech)
    print("Bullish Score:", score_res)
    assert score_res["total_score"] >= 80
    assert score_res["signal"] == "STRONG BUY"
    print("[OK] Test 1: Strong Bullish setup correctly achieved STRONG BUY.")

    # 2. Bearish Mock Tech Data
    bear_tech = {
        "ltp": 80.0,
        "sma_20": 95.0,
        "sma_50": 100.0,
        "sma_200": 110.0,
        "golden_cross": False,
        "rsi_14": 35.0,
        "macd_line": -2.0,
        "signal_line": -1.0,
        "macd_hist": -1.0,
        "hist_expanding": False,
        "vol_ratio": 0.4,
        "is_green_day": False,
        "is_breakout": False
    }
    bear_score = compute_technical_score(bear_tech)
    print("Bearish Score:", bear_score)
    assert bear_score["total_score"] < 20
    assert bear_score["signal"] == "STRONG SELL"
    print("[OK] Test 2: Bearish setup correctly achieved STRONG SELL.")

def test_live_report_generation():
    tickers = ["SQURPHARMA", "GP", "BATBC", "BRACBANK"]
    for t in tickers:
        rep = generate_trade_report(t)
        assert f"Ticker: {t}" in rep
        assert "Key Levels -> Entry:" in rep
        print(f"\n[Verified Live Report for {t}]:\n{rep}")

if __name__ == "__main__":
    print("=================================================================")
    print("TESTING STOCKNOW TECHNICAL TRADE SIGNAL AGENT")
    print("=================================================================")
    test_scoring_matrix()
    test_live_report_generation()
    print("\n=================================================================")
    print("ALL STOCKNOW AGENT TESTS COMPLETED SUCCESSFULLY!")
    print("=================================================================")
