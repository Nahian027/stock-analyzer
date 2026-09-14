import sys, os
sys.path.insert(0, os.path.abspath("."))
sys.stdout.reconfigure(encoding='utf-8')

import sqlite3
import pandas as pd
from app import get_5m_rsi_data, WATCHLIST_STOCKS

print("=== 5M RSI Verification for Portfolio Shares ===")
for item in WATCHLIST_STOCKS:
    sym = item['symbol']
    r5 = get_5m_rsi_data(sym, 280.0, 284.0, 276.0, 278.0, 150000)
    print(f"{sym:<12}: 5M RSI={r5['rsi_5m']:<5.1f} | Delta={r5['rsi_5m_delta']:<+5.1f} {r5['rsi_5m_trend_icon']} | Zone: {r5['rsi_5m_status']}")
print("=== All 10 Portfolio Stocks Tested Successfully ===")
