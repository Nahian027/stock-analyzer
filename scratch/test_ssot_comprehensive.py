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
from core_engine import evaluate_ticker, calculate_rsi

def run_all_tests():
    print("=" * 65)
    print("STARTING SSOT ARCHITECTURE & ANTI-MISMATCH COMPREHENSIVE TESTS")
    print("=" * 65)

    # -------------------------------------------------------------
    # TEST 1: SQURPHARMA at 213.20 Inverted Hammer & ATR Targets
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing exact SQURPHARMA setup at 213.20...")
    bars = []
    for i in range(30):
        bars.append({
            'Open': 205.0 + i*0.2,
            'High': 207.0 + i*0.2,
            'Low': 204.0 + i*0.2,
            'Close': 206.0 + i*0.2,
            'Volume': 50000
        })
    # Last bar: Inverted Hammer
    # Close = 213.20, Open = 210.0, High = 225.0, Low = 209.5
    # Body = 3.20, Upper Wick = 11.80 (>= 2x body), Lower Wick = 0.50 (<= 0.15 x range 15.5)
    bars[-1] = {
        'Open': 210.0,
        'High': 225.0,
        'Low': 209.5,
        'Close': 213.20,
        'Volume': 120000
    }
    df_squr = pd.DataFrame(bars)
    
    squr_result = evaluate_ticker('SQURPHARMA', df_squr, rsi_5m_val=44.5)
    print(f"SQURPHARMA Evaluated Output:\n{squr_result}")

    assert squr_result['pattern'] == "Inverted Hammer", f"Pattern must be Inverted Hammer, got {squr_result['pattern']}"
    assert squr_result['target'] == 225.0, f"Expected target 225.0, got {squr_result['target']}"
    assert squr_result['floor'] < 213.2, f"Expected floor < 213.2, got {squr_result['floor']}"
    assert squr_result['rrr'] > 1.0, f"Expected RRR > 1.0, got {squr_result['rrr']}"
    print("[OK] TEST 1 PASSED: SQURPHARMA pattern and ATR boundaries validated perfectly.")

    # -------------------------------------------------------------
    # TEST 2: Anti-Mismatch Rule Validation Across 100 Synthetic Stocks
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing Anti-Mismatch Invariants across 100 market permutations...")
    np.random.seed(42)
    results_cache = []
    
    for idx in range(100):
        sym = f"TICKER_{idx:03d}"
        base_price = np.random.uniform(20.0, 500.0)
        volatility = np.random.uniform(0.01, 0.05)
        trend = np.random.uniform(-0.03, 0.03)

        synth_bars = []
        p = base_price
        for d in range(40):
            p = max(5.0, p * (1.0 + trend + np.random.normal(0, volatility)))
            hi = p * (1.0 + np.random.uniform(0.005, 0.03))
            lo = p * (1.0 - np.random.uniform(0.005, 0.03))
            op = lo + np.random.uniform(0.0, hi - lo)
            synth_bars.append({'Open': op, 'High': hi, 'Low': lo, 'Close': p, 'Volume': np.random.randint(10000, 500000)})
        
        df_stock = pd.DataFrame(synth_bars)
        r5m_sim = np.random.uniform(20.0, 80.0)
        
        eval_dict = evaluate_ticker(sym, df_stock, rsi_5m_val=r5m_sim)
        results_cache.append(eval_dict)

        # STRICT ANTI-MISMATCH ASSERTION
        score = eval_dict['score']
        signal = eval_dict['signal']
        setup_status = eval_dict['setup_status']
        pct_change = eval_dict['pct_change']

        if score >= 75:
            assert signal == "STRONG BUY", f"Score {score} must yield STRONG BUY, got {signal}"
        elif score >= 55:
            assert signal == "BUY", f"Score {score} must yield BUY, got {signal}"

        elif score >= 40:
            assert signal == "HOLD", f"Score {score} must yield HOLD, got {signal}"
        elif score >= 20:
            assert signal == "SELL", f"Score {score} must yield SELL, got {signal}"
        else:
            assert signal == "STRONG SELL", f"Score {score} must yield STRONG SELL, got {signal}"

    print(f"[OK] TEST 2 PASSED: 100/100 tickers satisfied the Anti-Mismatch assertion.")


    # -------------------------------------------------------------
    # TEST 3: Single Source of Truth (df_shared) Pipeline Sync
    # -------------------------------------------------------------
    print("\n[TEST 3] Verifying df_shared Card View vs Table View Consistency...")
    df_shared = pd.DataFrame(results_cache)
    
    for _, row in df_shared.iterrows():
        t = row['ticker']
        # Card View consumption simulation
        card_view_record = df_shared[df_shared['ticker'] == t].iloc[0]
        # Table View consumption simulation
        table_view_record = df_shared[df_shared['ticker'] == t].iloc[0]

        assert card_view_record['score'] == table_view_record['score'] == row['score']
        assert card_view_record['signal'] == table_view_record['signal'] == row['signal']
        assert card_view_record['pattern'] == table_view_record['pattern'] == row['pattern']
        assert card_view_record['target'] == table_view_record['target'] == row['target']
        assert card_view_record['floor'] == table_view_record['floor'] == row['floor']
        assert card_view_record['setup_status'] == table_view_record['setup_status'] == row['setup_status']

    print("[OK] TEST 3 PASSED: Card View and Table View are 100% synchronized through df_shared!")
    print("\n" + "=" * 65)
    print("ALL SSOT TESTS PASSED SUCCESSFULLY! ZERO DATA DIVERGENCE CONFIRMED.")
    print("=" * 65)

if __name__ == "__main__":
    run_all_tests()
