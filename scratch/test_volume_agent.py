"""
Comprehensive Unit Test Suite for volume_agent.py.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from volume_agent import evaluate_institutional_entry, get_market_elapsed_minutes

def run_tests():
    print("=" * 65)
    print("STARTING VOLUME & REGIME CONFIRMATION AGENT UNIT TESTS")
    print("=" * 65)

    # 1. Test Elapsed Time Normalization
    elapsed_morning = get_market_elapsed_minutes(pd.Timestamp("2026-09-15 10:30:00"))
    assert elapsed_morning == 30, f"Expected 30 mins, got {elapsed_morning}"
    
    elapsed_afternoon = get_market_elapsed_minutes(pd.Timestamp("2026-09-15 14:15:00"))
    assert elapsed_afternoon == 240, f"Expected 240 mins, got {elapsed_afternoon}"
    print("[OK] Test 1: Market elapsed time helper calculated correctly.")

    # 2. Test Breakdown Scenario (Price < Support * 0.992)
    # Support = 5400, Price = 5350 (-0.93% below support)
    res_breakdown = evaluate_institutional_entry(
        current_price=5350.0,
        support_level=5400.0,
        df_intraday=None,
        df_daily=None,
        market_turnover_cr=600.0,
        market_hours_elapsed_mins=120
    )
    print(f"Breakdown Output: Command='{res_breakdown['command']}', Confidence={res_breakdown['confidence_score']}%")
    assert res_breakdown['decision'] == "ABORT_BREAKDOWN"
    assert res_breakdown['command'] == "ABORT TRADE"
    assert res_breakdown['color'] == "#D50000"
    assert res_breakdown['confidence_score'] == 0
    print("[OK] Test 2: Breakdown scenario yields unequivocal 'ABORT TRADE' with 0% confidence.")

    # 3. Test Confirmed Institutional Accumulation (In Demand Pocket, High Projected Volume >= 1.30x, Bullish Candles)
    df_daily_high_vol = pd.DataFrame([
        {'Volume': 50000000} for _ in range(20)
    ] + [{'Volume': 35000000}]) # Current vol at 60 mins into session (35M / (60/240) = 140M projected -> 2.8x)
    
    df_intra_bull = pd.DataFrame([
        {'Open': 5402, 'High': 5406, 'Low': 5400, 'Close': 5405, 'Volume': 500000},
        {'Open': 5405, 'High': 5410, 'Low': 5404, 'Close': 5409, 'Volume': 600000},
        {'Open': 5409, 'High': 5415, 'Low': 5408, 'Close': 5414, 'Volume': 700000}
    ])

    res_confirmed = evaluate_institutional_entry(
        current_price=5405.0, # Exactly in demand pocket (-0.5% to +1.0% of 5400)
        support_level=5400.0,
        df_intraday=df_intra_bull,
        df_daily=df_daily_high_vol,
        market_turnover_cr=650.0,
        market_hours_elapsed_mins=60
    )
    print(f"Confirmed Execution Output: Command='{res_confirmed['command']}', Confidence={res_confirmed['confidence_score']}%, VolRatio={res_confirmed['projected_vol_ratio']}x")
    assert res_confirmed['decision'] == "CONFIRMED_EXECUTION"
    assert res_confirmed['command'] == "BUY NOW"
    assert res_confirmed['color'] == "#00C853"
    assert res_confirmed['confidence_score'] == 95
    print("[OK] Test 3: Confirmed execution yields 'BUY NOW' with 95% confidence and Emerald Green banding.")

    # 4. Test Moderate Accumulation (Volume Ratio ~1.0x to 1.29x)
    df_daily_mod_vol = pd.DataFrame([
        {'Volume': 50000000} for _ in range(20)
    ] + [{'Volume': 27000000}]) # 27M / (120/240) = 54M projected -> 1.08x

    res_moderate = evaluate_institutional_entry(
        current_price=5410.0,
        support_level=5400.0,
        df_intraday=df_intra_bull,
        df_daily=df_daily_mod_vol,
        market_turnover_cr=550.0,
        market_hours_elapsed_mins=120
    )
    print(f"Moderate Accumulation Output: Command='{res_moderate['command']}', Confidence={res_moderate['confidence_score']}%, VolRatio={res_moderate['projected_vol_ratio']}x")
    assert res_moderate['decision'] == "MODERATE_ACCUMULATION"
    assert res_moderate['command'] == "ACCUMULATE 30%"
    assert res_moderate['color'] == "#1E88E5"
    assert res_moderate['confidence_score'] == 65
    print("[OK] Test 4: Moderate volume yields 'ACCUMULATE 30%' with 65% confidence and Dodger Blue banding.")

    # 5. Test No Volume Trap / Dead-Cat Bounce (Volume < 1.0x in demand pocket)
    df_daily_low_vol = pd.DataFrame([
        {'Volume': 50000000} for _ in range(20)
    ] + [{'Volume': 5000000}]) # 5M / (120/240) = 10M projected -> 0.20x

    res_trap = evaluate_institutional_entry(
        current_price=5402.0,
        support_level=5400.0,
        df_intraday=None,
        df_daily=df_daily_low_vol,
        market_turnover_cr=300.0,
        market_hours_elapsed_mins=120
    )
    print(f"No Volume Trap Output: Command='{res_trap['command']}', Confidence={res_trap['confidence_score']}%, VolRatio={res_trap['projected_vol_ratio']}x")
    assert res_trap['decision'] == "NO_VOLUME_TRAP"
    assert res_trap['command'] == "HOLD CASH"
    assert res_trap['color'] == "#FFB300"
    assert res_trap['confidence_score'] == 25
    print("[OK] Test 5: Low volume dead-cat bounce trap yields 'HOLD CASH' with Amber banding.")

    # 6. Test Out of Demand Zone (Price well above support)
    res_await = evaluate_institutional_entry(
        current_price=5480.0, # +80 pts above support
        support_level=5400.0,
        df_intraday=None,
        df_daily=None,
        market_turnover_cr=600.0,
        market_hours_elapsed_mins=120
    )
    print(f"Await Correction Output: Command='{res_await['command']}', Confidence={res_await['confidence_score']}%")
    assert res_await['decision'] == "AWAIT_CORRECTION"
    assert res_await['command'] == "HOLD CASH"
    print("[OK] Test 6: Await correction correctly commands 'HOLD CASH' when far from support.")

    print("\n" + "=" * 65)
    print("ALL VOLUME & REGIME AGENT TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
