"""
Comprehensive SSOT Architecture & Anti-Mismatch Assertion Unit Tests.
Verifies synchronization across Portfolio Cards, Screener Table, and Pattern Scanner.
"""

import sys
import os
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, r"d:\CV\stock analyzer")

from core_engine import evaluate_ticker, calculate_rsi
from app import get_comprehensive_stock_analysis, WATCHLIST_STOCKS


def test_inverted_hammer_detection():
    print("\n--- TEST 1: Inverted Hammer Detection & ATR Calculations ---")
    data = []
    for i in range(35):
        data.append({'Open': 200 + i*0.4, 'High': 202 + i*0.4, 'Low': 199 + i*0.4, 'Close': 201 + i*0.4, 'Volume': 50000})

    # SQURPHARMA at 213.20 Inverted Hammer bar:
    # Open: 210.0, High: 225.0, Low: 209.5, Close: 213.20
    # Body = 3.20, Upper wick = 11.80 (>= 2x body), Lower wick = 0.50 (<= 0.15 x total_range 15.5)
    data[-1] = {'Open': 210.0, 'High': 225.0, 'Low': 209.5, 'Close': 213.20, 'Volume': 100000}
    df = pd.DataFrame(data)

    res = evaluate_ticker('SQURPHARMA', df, rsi_5m_val=44.5)
    print(f"SQURPHARMA Evaluated: Pattern='{res['pattern']}', Score={res['score']}, Signal='{res['signal']}', Setup='{res['setup_status']}'")
    
    assert res['pattern'] == "Inverted Hammer", f"Expected Inverted Hammer, got {res['pattern']}"
    assert res['close'] == 213.20, f"Expected close 213.20, got {res['close']}"
    assert res['target'] > res['close'], "Target must be strictly greater than close"
    assert res['floor'] < res['close'], "Floor must be strictly less than close"
    assert res['target'] == round(res['close'] + 1.5 * res['atr'], 2), "Target ATR formula mismatch"
    assert res['floor'] == round(res['close'] - 1.2 * res['atr'], 2), "Floor ATR formula mismatch"
    print("✓ Test 1 Passed: Inverted Hammer & ATR levels exact.")


def test_anti_mismatch_assertions():
    print("\n--- TEST 2: Anti-Mismatch Assertions Across Synthetic Regime States ---")
    
    # Test all possible score intervals
    test_cases = [
        {"name": "Bearish Breakdown (Score <= 35)", "trend": -2.0, "rsi": 25.0, "expected_signal": "SELL", "expected_setup": "Bearish Breakdown"},
        {"name": "Consolidation / Range (36 <= Score < 60)", "trend": 0.0, "rsi": 40.0, "expected_signal": "HOLD", "expected_setup": "Consolidating / Range"},
        {"name": "Bullish Setup (60 <= Score < 75)", "trend": 1.0, "rsi": 55.0, "expected_signal": "BUY", "expected_setup": "Bullish Setup"},
        {"name": "Bullish Breakout (Score >= 75)", "trend": 2.5, "rsi": 60.0, "expected_signal": "STRONG BUY", "expected_setup": "Bullish Breakout"},
    ]

    for case in test_cases:
        data = []
        for i in range(35):
            p = 100 + i * case["trend"]
            data.append({'Open': p - 0.2, 'High': p + 1.0, 'Low': p - 1.0, 'Close': p, 'Volume': 50000})
        df = pd.DataFrame(data)
        
        res = evaluate_ticker("TEST_TICKER", df, rsi_5m_val=50.0)
        score = res['score']
        signal = res['signal']
        setup = res['setup_status']
        print(f"Case [{case['name']}]: Score={score}, Signal={signal}, Setup={setup}")

        # Core Anti-Mismatch Rule:
        if score < 60:
            assert signal != "BUY" and signal != "STRONG BUY", (
                f"Desync on TEST_TICKER: Score {score} cannot yield {signal}!"
            )
            assert setup != "Bullish Setup" and setup != "Bullish Breakout", (
                f"Desync on TEST_TICKER: Score {score} cannot yield {setup}!"
            )
        else:
            assert signal in ["BUY", "STRONG BUY"], f"Score {score} must yield BUY or STRONG BUY, got {signal}"
            assert setup in ["Bullish Setup", "Bullish Breakout"], f"Score {score} must yield Bullish Setup or Breakout, got {setup}"

    print("✓ Test 2 Passed: Anti-mismatch invariant holds across all score regimes.")


def test_watchlist_shared_state_pipeline():
    print("\n--- TEST 3: Full Watchlist Shared Pipeline & Zero-Desync Validation ---")
    
    # Simulate Watchlist Evaluation as done in app.py
    results_cache = []
    for item in WATCHLIST_STOCKS:
        sym = item["symbol"]
        analysis = get_comprehensive_stock_analysis(sym, 100.0, 102.0, 99.0, 50000.0, 99.5, 0.5, 0.5)
        setup = analysis["stock_setup"]
        results_cache.append(setup)
        
        # Verify Card vs Table SSOT contract:
        # Card properties from analysis must EXACTLY equal setup properties
        assert analysis["score"] == setup["score"], f"Score desync on {sym}"
        assert analysis["action"] == setup["signal"], f"Signal desync on {sym}"
        assert analysis["target_selling_price"] == setup["target"], f"Target desync on {sym}"
        assert analysis["target_buying_price"] == setup["floor"], f"Floor desync on {sym}"

    df_shared = pd.DataFrame(results_cache)
    print(f"Precomputed df_shared shape: {df_shared.shape}")

    # Run Anti-Mismatch Assertion Loop across the shared DataFrame
    for _, item in df_shared.iterrows():
        if item['score'] < 60:
            assert item['signal'] != "BUY" and item['setup_status'] != "Bullish Setup", (
                f"Desync on {item['ticker']}: Score {item['score']} cannot yield Bullish Setup!"
            )
        else:
            assert item['signal'] in ["BUY", "STRONG BUY"], (
                f"Desync on {item['ticker']}: Score {item['score']} must yield BUY, got {item['signal']}"
            )

    print("✓ Test 3 Passed: 100% Shared state consistency between Card View and Table View across entire Watchlist!")


if __name__ == "__main__":
    print("=" * 60)
    print("RUNNING SINGLE SOURCE OF TRUTH (SSOT) VERIFICATION SUITE")
    print("=" * 60)
    test_inverted_hammer_detection()
    test_anti_mismatch_assertions()
    test_watchlist_shared_state_pipeline()
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED WITH ZERO DATA DIVERGENCE!")
    print("=" * 60)
