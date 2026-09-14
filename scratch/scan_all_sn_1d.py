import sys
sys.path.insert(0, r"d:\CV\stock analyzer")
import pandas as pd
from app import fetch_authentic_history, detect_candlestick_triggers, detect_candlestick_patterns_history, BEST_15_UNIVERSE, WATCHLIST_STOCKS

all_symbols = list(set([item["symbol"] for item in BEST_15_UNIVERSE] + [item["symbol"] for item in WATCHLIST_STOCKS]))
all_symbols.sort()

print(f"--- SCANNING ALL {len(all_symbols)} DSE INSTRUMENTS WITH STOCKNOW 1D FEED ---")

detected_summary = []

for sym in all_symbols:
    try:
        df = fetch_authentic_history(sym, days=180)
        if df.empty or len(df) < 5:
            print(f"[{sym}] No sufficient 1D data")
            continue
        
        triggers = detect_candlestick_triggers(df)
        history_pats = detect_candlestick_patterns_history(df, max_lookback=60)
        
        last_dt = df.index[-1].strftime('%Y-%m-%d')
        o, h, l, c = df['open'].iloc[-1], df['high'].iloc[-1], df['low'].iloc[-1], df['close'].iloc[-1]
        
        trig_names = [f"{t['bias'].upper()}: {t['name']}" for t in triggers] if triggers else ["None (Neutral)"]
        
        detected_summary.append({
            "symbol": sym,
            "date": last_dt,
            "ohlc": f"O={o} H={h} L={l} C={c}",
            "triggers": ", ".join(trig_names),
            "recent_count": len(history_pats),
            "latest_hist_pat": f"{history_pats[-1]['name']} ({history_pats[-1]['date'].strftime('%Y-%m-%d')})" if history_pats else "None"
        })
    except Exception as e:
        print(f"[{sym}] Error: {e}")

df_res = pd.DataFrame(detected_summary)
print(df_res.to_string(index=False))
print("\n--- ALL STOCKNOW 1D CANDLESTICK SCANS FINISHED SUCCESSFULLY ---")
