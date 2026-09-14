import sys, requests, json, datetime as dt, pandas as pd, urllib3
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://stocknow.com.bd/'
}

def fetch_stocknow_1d(symbol: str, days: int = 365) -> pd.DataFrame:
    url = f"https://stocknow.com.bd/api/v1/instruments/{symbol}/history?data2=true&resolution=1D"
    res = requests.get(url, headers=headers, verify=False, timeout=8)
    data = res.json()
    opens, highs, lows, closes, vols, timestamps = data[0], data[1], data[2], data[3], data[4], data[5]
    n = len(timestamps)
    df = pd.DataFrame({
        'open': [float(x) for x in opens[:n]],
        'high': [float(x) for x in highs[:n]],
        'low': [float(x) for x in lows[:n]],
        'close': [float(x) for x in closes[:n]],
        'volume': [float(x) for x in vols[:n]],
    }, index=pd.to_datetime([int(ts) for ts in timestamps[:n]], unit='s'))
    df = df[(df['open'] > 0) & (df['high'] > 0) & (df['low'] > 0) & (df['close'] > 0)]
    df.sort_index(ascending=True, inplace=True)
    return df

# Test on 5 stocks
for sym in ['GP', 'SQURPHARMA', 'BATBC', 'BRACBANK', 'LHB']:
    df = fetch_stocknow_1d(sym)
    print(f"=== Testing Candlestick Accuracy on {sym} ({len(df)} 1D bars) ===")
    
    # Calculate ATR
    tr = pd.concat([df['high'] - df['low'], (df['high'] - df['close'].shift(1)).abs(), (df['low'] - df['close'].shift(1)).abs()], axis=1).max(axis=1)
    df['ATR'] = tr.ewm(alpha=1/14, min_periods=5, adjust=False).mean()
    df['Vol_SMA_20'] = df['volume'].rolling(window=20, min_periods=5).mean()
    
    # Look back 60 days
    sub = df.iloc[-60:]
    detected = []
    for i in range(2, len(sub)):
        curr = sub.iloc[i]
        prev = sub.iloc[i-1]
        prev2 = sub.iloc[i-2]
        date = sub.index[i].strftime('%Y-%m-%d')
        
        co, cc, ch, cl = curr['open'], curr['close'], curr['high'], curr['low']
        po, pc, ph, pl = prev['open'], prev['close'], prev['high'], prev['low']
        p2o, p2c, p2h, p2l = prev2['open'], prev2['close'], prev2['high'], prev2['low']
        
        c_body = abs(cc - co)
        c_range = ch - cl + 1e-9
        p_body = abs(pc - po)
        p_range = ph - pl + 1e-9
        p2_body = abs(p2c - p2o)
        
        c_green = cc > co
        p_green = pc > po
        p2_green = p2c > p2o
        
        lower_shadow = min(co, cc) - cl
        upper_shadow = ch - max(co, cc)
        atr = curr['ATR']
        
        # Recent swing context
        recent_low = sub['low'].iloc[max(0, i-6):i].min()
        recent_high = sub['high'].iloc[max(0, i-6):i].max()
        is_at_dip = cl <= recent_low * 1.015
        is_at_peak = ch >= recent_high * 0.985
        
        # 1. Bullish Engulfing
        if not p_green and c_green and co <= pc + 0.05 * p_body and cc >= po - 0.05 * p_body and c_body > p_body and p_body >= 0.2 * p_range and is_at_dip:
            detected.append((date, 'Bullish Engulfing', 'Bullish', cc))
        
        # 2. Bearish Engulfing
        elif p_green and not c_green and co >= pc - 0.05 * p_body and cc <= po + 0.05 * p_body and c_body > p_body and p_body >= 0.2 * p_range and is_at_peak:
            detected.append((date, 'Bearish Engulfing', 'Bearish', cc))
        
        # 3. Hammer
        elif lower_shadow >= 2.0 * c_body and upper_shadow <= (0.25 * c_body + 0.05 * c_range) and is_at_dip:
            detected.append((date, 'Hammer (Pinbar)', 'Bullish', cc))
        
        # 4. Shooting Star
        elif upper_shadow >= 2.0 * c_body and lower_shadow <= (0.25 * c_body + 0.05 * c_range) and is_at_peak:
            detected.append((date, 'Shooting Star', 'Bearish', cc))
        
        # 5. Morning Star
        elif not p2_green and p2_body >= 0.4 * (p2h - p2l) and p_body <= 0.45 * p2_body and c_green and cc >= p2c + 0.5 * (p2o - p2c):
            detected.append((date, 'Morning Star', 'Bullish', cc))
        
        # 6. Evening Star
        elif p2_green and p2_body >= 0.4 * (p2h - p2l) and p_body <= 0.45 * p2_body and not c_green and cc <= p2o + 0.5 * (p2c - p2o):
            detected.append((date, 'Evening Star', 'Bearish', cc))
        
        # 7. Piercing Line
        elif not p_green and p_body >= 0.35 * p_range and c_green and co <= pc and cc >= pc + 0.5 * p_body and cc < po and is_at_dip:
            detected.append((date, 'Piercing Line', 'Bullish', cc))
        
        # 8. Dark Cloud Cover
        elif p_green and p_body >= 0.35 * p_range and not c_green and co >= pc and cc <= pc - 0.5 * p_body and cc > po and is_at_peak:
            detected.append((date, 'Dark Cloud Cover', 'Bearish', cc))
        
        # 9. Dragonfly Doji
        elif c_body / c_range <= 0.08 and lower_shadow >= 0.65 * c_range and is_at_dip:
            detected.append((date, 'Dragonfly Doji', 'Bullish', cc))
        
        # 10. Gravestone Doji
        elif c_body / c_range <= 0.08 and upper_shadow >= 0.65 * c_range and is_at_peak:
            detected.append((date, 'Gravestone Doji', 'Bearish', cc))
        
        # 11. Doji
        elif c_body / c_range <= 0.08 and c_range >= 0.005 * cc:
            detected.append((date, 'Doji Candle', 'Neutral', cc))

    print(f"Patterns detected in last 60 days: {len(detected)}")
    for d, name, bias, price in detected[-6:]:
        print(f"  {d} | {name:<22} | {bias:<8} | Tk {price:.1f}")
