import sys, requests, json, datetime as dt, pandas as pd, urllib3
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://stocknow.com.bd/'
}

def fetch_stocknow_1d_history(symbol: str, days: int = 365) -> pd.DataFrame:
    symbol = symbol.upper().strip()
    url = f"https://stocknow.com.bd/api/v1/instruments/{symbol}/history?data2=true&resolution=1D"
    try:
        res = requests.get(url, headers=headers, verify=False, timeout=8)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list) and len(data) >= 6:
                opens, highs, lows, closes, vols, timestamps = data[0], data[1], data[2], data[3], data[4], data[5]
                n = len(timestamps)
                if n > 0:
                    df = pd.DataFrame({
                        'open': [float(x) for x in opens[:n]],
                        'high': [float(x) for x in highs[:n]],
                        'low': [float(x) for x in lows[:n]],
                        'close': [float(x) for x in closes[:n]],
                        'volume': [float(x) for x in vols[:n]],
                    }, index=pd.to_datetime([int(ts) for ts in timestamps[:n]], unit='s'))
                    
                    df.sort_index(ascending=True, inplace=True)
                    df = df[(df['open'] > 0) & (df['high'] > 0) & (df['low'] > 0) & (df['close'] > 0)]
                    if days and len(df) > 0:
                        cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
                        df = df[df.index >= cutoff]
                    return df
    except Exception as e:
        print(f"Error fetching StockNow 1D for {symbol}:", e)
    return pd.DataFrame()

symbols = ['GP', 'SQURPHARMA', 'BATBC', 'BRACBANK', 'WALTONHIL']
for s in symbols:
    df = fetch_stocknow_1d_history(s, days=365)
    print(f"{s:<10}: {len(df)} candles fetched | Range: {df.index[0].date()} to {df.index[-1].date()} | Latest Close: Tk {df['close'].iloc[-1]:.2f}")
