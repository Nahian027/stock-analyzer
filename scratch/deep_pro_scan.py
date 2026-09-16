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
from stocknow_agent import fetch_ticker_data_stocknow
from core_engine import evaluate_ticker, calculate_rsi

TICKERS = [
    ("SQURPHARMA", "Square Pharmaceuticals Ltd.", "Pharma"),
    ("BATBC", "British American Tobacco BD", "Food & Allied"),
    ("GP", "Grameenphone Ltd.", "Telecommunication"),
    ("BRACBANK", "BRAC Bank PLC", "Banking"),
    ("WALTONHIL", "Walton Hi-Tech Industries", "Engineering"),
    ("SONARBAINS", "Sonar Bangla Insurance Ltd.", "Insurance"),
    ("ACMELAB", "The ACME Laboratories Ltd.", "Pharma"),
    ("ACI", "ACI Limited", "Pharma & Chemical"),
    ("IDLC", "IDLC Finance Ltd.", "Financial Inst."),
    ("LHBL", "LafargeHolcim Bangladesh PLC", "Cement"),
    ("BEXIMCO", "Beximco Ltd.", "Diversified"),
    ("ROBI", "Robi Axiata Ltd.", "Telecommunication")
]

def run_deep_pro_scan():
    full_reports = []
    
    for sym, name, sector in TICKERS:
        df = fetch_ticker_data_stocknow(sym)
        if df is None or len(df) < 15:
            # Fallback for Lafarge
            if sym == "LHBL":
                df = fetch_ticker_data_stocknow("LAFSURCEML")
        
        if df is None or len(df) < 15:
            continue
            
        # SSOT Engine evaluation
        res = evaluate_ticker(sym, df)
        
        # MACD calculation
        close_s = df['close'] if 'close' in df.columns else df['Close']
        ema_12 = close_s.ewm(span=12, adjust=False).mean()
        ema_26 = close_s.ewm(span=26, adjust=False).mean()
        macd_line = float((ema_12 - ema_26).iloc[-1])
        signal_line = float((ema_12 - ema_26).ewm(span=9, adjust=False).mean().iloc[-1])
        macd_hist = macd_line - signal_line
        
        # 50 SMA & 200 SMA
        sma_50 = float(close_s.rolling(50, min_periods=min(10, len(close_s))).mean().iloc[-1])
        sma_200 = float(close_s.rolling(200, min_periods=min(30, len(close_s))).mean().iloc[-1]) if len(close_s) >= 40 else sma_50
        
        res["name"] = name
        res["sector"] = sector
        res["macd_line"] = round(macd_line, 3)
        res["signal_line"] = round(signal_line, 3)
        res["macd_hist"] = round(macd_hist, 3)
        res["sma_50"] = round(sma_50, 2)
        res["sma_200"] = round(sma_200, 2)
        
        full_reports.append(res)
        
    return full_reports

if __name__ == "__main__":
    reports = run_deep_pro_scan()
    print("=== DEEP QUANTITATIVE SCAN COMPLETE ===")
    for r in reports:
        print(f"[{r['ticker']}] {r['name']} ({r['sector']})")
        print(f"  LTP: {r['close']} ({r['pct_change']:+.2f}%) | Score: {r['score']}/100 | Signal: {r['signal']} ({r['setup_status']})")
        print(f"  Pattern: {r['pattern']} ({r['pattern_bias']}) | RSI(14): {r['rsi_1d']} | Vol Ratio: {r['vol_ratio']}x")
        print(f"  20 EMA: {r['ema_20']} | 50 SMA: {r['sma_50']} | 200 SMA: {r['sma_200']}")
        print(f"  MACD Line: {r['macd_line']} | Signal Line: {r['signal_line']} | Hist: {r['macd_hist']:+.3f}")
        print(f"  Key Levels -> Support Floor: {r['floor']} ({r['floor_pct']:+.1f}%) | Resistance Target: {r['target']} ({r['target_pct']:+.1f}%) | RRR: 1:{r['rrr']}")
        print(f"  Next Move Bias: {r['next_move']['direction_text']} -> Tk {r['next_move']['target_price']} ({r['next_move']['delta_pct']})")
        print("-" * 80)
