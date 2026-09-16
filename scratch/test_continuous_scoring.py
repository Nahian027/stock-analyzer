"""
Validation Suite for Continuous Normalized Composite Scoring, Dynamic RRR, and Rational Signals.
"""

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
from core_engine import evaluate_ticker, calculate_composite_score, calculate_rsi

def test_rebounding_green_days():
    print("\n--- TEST 1: Green / Rebounding Days (BATBC +2.71%, SONARBAINS +5.20%) ---")
    
    # 1. Simulate BATBC (+2.71% green rebound day)
    bars_batbc = []
    p = 380.0
    for i in range(35):
        p = 380.0 - (i * 0.5) # declining trend
        bars_batbc.append({'Open': p, 'High': p + 2, 'Low': p - 2, 'Close': p, 'Volume': 40000})
    # Rebound today: close 372.0 (+2.71% from 362.18)
    prev_c = bars_batbc[-2]['Close']
    today_c = round(prev_c * 1.0271, 2)
    bars_batbc[-1] = {'Open': prev_c, 'High': today_c + 3, 'Low': prev_c - 1, 'Close': today_c, 'Volume': 90000}
    df_batbc = pd.DataFrame(bars_batbc)
    
    res_batbc = evaluate_ticker('BATBC', df_batbc)
    print(f"BATBC (+2.71% Rebound): Score={res_batbc['score']}/100, Signal={res_batbc['signal']}, Pattern={res_batbc['pattern']}, RRR=1:{res_batbc['rrr']}")
    
    assert res_batbc['signal'] != "SELL", f"Green rebounding day (+2.71%) must NOT issue SELL! Got {res_batbc['signal']}"
    assert res_batbc['score'] >= 35, f"Score should not zero out on rebound day! Got {res_batbc['score']}"

    # 2. Simulate SONARBAINS (+5.20% strong surge day)
    bars_sonar = []
    p = 45.0
    for i in range(35):
        p = 45.0 + (i * 0.1)
        bars_sonar.append({'Open': p, 'High': p + 0.5, 'Low': p - 0.5, 'Close': p, 'Volume': 50000})
    prev_c = bars_sonar[-2]['Close']
    today_c = round(prev_c * 1.0520, 2)
    bars_sonar[-1] = {'Open': prev_c, 'High': today_c + 1.0, 'Low': prev_c, 'Close': today_c, 'Volume': 180000}
    df_sonar = pd.DataFrame(bars_sonar)

    res_sonar = evaluate_ticker('SONARBAINS', df_sonar)
    print(f"SONARBAINS (+5.20% Surge): Score={res_sonar['score']}/100, Signal={res_sonar['signal']}, Pattern={res_sonar['pattern']}, RRR=1:{res_sonar['rrr']}")

    assert res_sonar['signal'] in ["BUY", "STRONG BUY"], f"Strong surge (+5.20%) with volume must yield BUY or STRONG BUY! Got {res_sonar['signal']}"
    assert res_sonar['score'] >= 55, f"Score must be >= 55 for surge stock! Got {res_sonar['score']}"
    print("[OK] TEST 1 PASSED: Green rebound days correctly rewarded, zero premature SELLs.")


def test_no_pattern_continuity():
    print("\n--- TEST 2: Absence of Candlestick Pattern does NOT zero-out score ---")
    bars = []
    p = 150.0
    for i in range(40):
        p = 150.0 + (i * 0.3)
        bars.append({'Open': p - 0.1, 'High': p + 0.8, 'Low': p - 0.8, 'Close': p, 'Volume': 60000})
    # Last bar: Normal spinning top / no distinctive pattern
    bars[-1] = {'Open': p - 0.2, 'High': p + 0.5, 'Low': p - 0.5, 'Close': p + 0.2, 'Volume': 70000}
    df = pd.DataFrame(bars)

    res = evaluate_ticker('NORMAL_STOCK', df)
    print(f"NORMAL_STOCK (No Pattern): Pattern='{res['pattern']}', Score={res['score']}/100, Signal={res['signal']}")
    
    assert res['pattern'] == "No Distinct Pattern"
    # Trend is up, day is positive, volume is solid -> Score should comfortably be in 55-75 range!
    assert res['score'] >= 50, f"Stock with solid trend must not be penalized for lacking pattern! Got {res['score']}"
    assert res['signal'] in ["BUY", "HOLD"], f"Expected BUY or HOLD, got {res['signal']}"
    print("[OK] TEST 2 PASSED: Absence of pattern handled gracefully as expected.")


def test_dynamic_rrr_variation():
    print("\n--- TEST 3: Dynamic Risk-to-Reward Ratio (Stop static 1:1.20) ---")
    
    # 1. Pullback stock with high overhead resistance (Wide upside, tight support)
    # Peak at 150, current close at 120, support at 115
    bars_wide_up = []
    for i in range(20):
        bars_wide_up.append({'Open': 140, 'High': 150, 'Low': 138, 'Close': 145, 'Volume': 50000})
    for i in range(15):
        p = 145 - i * 1.6
        bars_wide_up.append({'Open': p, 'High': p + 1, 'Low': p - 1, 'Close': p, 'Volume': 50000})
    df_wide_up = pd.DataFrame(bars_wide_up)
    res_wide_up = evaluate_ticker('WIDE_UPSIDE_STOCK', df_wide_up)
    print(f"Wide Upside Stock: Close={res_wide_up['close']}, Target={res_wide_up['target']}, Floor={res_wide_up['floor']}, RRR=1:{res_wide_up['rrr']}")

    # 2. Breakout stock at new highs
    bars_breakout = []
    for i in range(35):
        p = 100 + i * 1.2
        bars_breakout.append({'Open': p - 0.5, 'High': p + 1.0, 'Low': p - 0.5, 'Close': p, 'Volume': 80000})
    df_breakout = pd.DataFrame(bars_breakout)
    res_breakout = evaluate_ticker('BREAKOUT_STOCK', df_breakout)
    print(f"Breakout Stock: Close={res_breakout['close']}, Target={res_breakout['target']}, Floor={res_breakout['floor']}, RRR=1:{res_breakout['rrr']}")

    # 3. Range-bound stock near ceiling (Tight upside, wide downside)
    bars_tight_up = []
    for i in range(20):
        bars_tight_up.append({'Open': 100, 'High': 120, 'Low': 95, 'Close': 105, 'Volume': 50000})
    for i in range(15):
        p = 105 + i * 1.0
        bars_tight_up.append({'Open': p, 'High': p + 0.5, 'Low': p - 0.5, 'Close': p, 'Volume': 50000})
    df_tight_up = pd.DataFrame(bars_tight_up)
    res_tight_up = evaluate_ticker('TIGHT_UPSIDE_STOCK', df_tight_up)
    print(f"Tight Upside Stock: Close={res_tight_up['close']}, Target={res_tight_up['target']}, Floor={res_tight_up['floor']}, RRR=1:{res_tight_up['rrr']}")

    rrr_list = [res_wide_up['rrr'], res_breakout['rrr'], res_tight_up['rrr']]
    print(f"Collected RRR values: {rrr_list}")
    assert len(set(rrr_list)) >= 2, f"RRR must be dynamic and vary across structural charts, got {rrr_list}"
    print("[OK] TEST 3 PASSED: Dynamic RRR verified across varying volatility/pivot charts.")


if __name__ == "__main__":
    print("=" * 65)
    print("CONTINUOUS SCORING & DYNAMIC RRR VERIFICATION")
    print("=" * 65)
    test_rebounding_green_days()
    test_no_pattern_continuity()
    test_dynamic_rrr_variation()
    print("\n" + "=" * 65)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)
