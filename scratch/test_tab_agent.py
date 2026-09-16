import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import pandas as pd
from stocknow_agent import fetch_ticker_data_stocknow, calculate_technical_indicators
from core_engine import evaluate_ticker

def test_agent_scanner():
    watchlist = ["SQURPHARMA", "WALTONHIL", "BATBC", "GP", "BRACBANK", "ACI", "ACMELAB", "IDLC", "LHBL", "SONARBAINS", "BEXIMCO", "ROBI"]
    
    buy_orders = []
    hold_orders = []
    sell_orders = []
    
    for sym in watchlist:
        df = fetch_ticker_data_stocknow(sym)
        if df is None or len(df) < 10:
            if sym == "LHBL":
                df = fetch_ticker_data_stocknow("LAFSURCEML")
        if df is not None and len(df) >= 10:
            res = evaluate_ticker(sym, df)
            if res["score"] >= 60:
                buy_orders.append(res)
            elif res["score"] >= 40:
                hold_orders.append(res)
            else:
                sell_orders.append(res)
                
    print(f"Buy Orders ({len(buy_orders)}): {[b['ticker'] for b in buy_orders]}")
    print(f"Hold Orders ({len(hold_orders)}): {[h['ticker'] for h in hold_orders]}")
    print(f"Sell Orders ({len(sell_orders)}): {[s['ticker'] for s in sell_orders]}")
    
    assert len(buy_orders) > 0, "Should have at least one buy order"
    print("[OK] Autonomous agent scanner logic verified.")

if __name__ == "__main__":
    test_agent_scanner()
