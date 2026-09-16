import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import pandas as pd
from stocknow_agent import fetch_ticker_data_stocknow
from core_engine import evaluate_ticker

WATCHLIST = [
    "GP", "SQURPHARMA", "BATBC", "BRACBANK", "ACI", 
    "ACMELAB", "IDLC", "LHBL", "WALTONHIL", "SONARBAINS", "BEXIMCO", "ROBI"
]

def scan_all():
    results = []
    for sym in WATCHLIST:
        df = fetch_ticker_data_stocknow(sym)
        if df is not None and len(df) >= 10:
            res = evaluate_ticker(sym, df)
            results.append(res)
        else:
            # Try alt symbol
            if sym == "LHBL":
                df = fetch_ticker_data_stocknow("LAFSURCEML")
                if df is not None:
                    results.append(evaluate_ticker("LHBL", df))
    
    print(f"{'TICKER':<12} | {'LTP':<8} | {'CHG%':<7} | {'SCORE':<7} | {'SIGNAL':<12} | {'PATTERN':<18} | {'FLOOR':<8} | {'TARGET':<8} | {'RRR'}")
    print("-" * 105)
    for r in results:
        print(f"{r['ticker']:<12} | {r['close']:<8.2f} | {r['pct_change']:<+6.2f}% | {r['score']:<3}/100 | {r['signal']:<12} | {r['pattern']:<18} | {r['floor']:<8.2f} | {r['target']:<8.2f} | 1:{r['rrr']}")

if __name__ == "__main__":
    scan_all()
