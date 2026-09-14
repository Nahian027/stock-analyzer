import sys, requests, json, datetime as dt, pandas as pd, urllib3
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://stocknow.com.bd/'
}

def fetch_stocknow_1d(symbol: str) -> pd.DataFrame:
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

def detect_candlestick_patterns_history(df: pd.DataFrame, max_lookback: int = 60) -> list:
    results = []
    if len(df) < 3:
        return results

    sub_df = df.iloc[-max_lookback:] if len(df) > max_lookback else df

    for i in range(1, len(sub_df)):
        curr = sub_df.iloc[i]
        prev = sub_df.iloc[i-1]
        date = sub_df.index[i]
        
        c_open, c_close, c_high, c_low = float(curr['open']), float(curr['close']), float(curr['high']), float(curr['low'])
        p_open, p_close, p_high, p_low = float(prev['open']), float(prev['close']), float(prev['high']), float(prev['low'])
        c_vol = float(curr.get('volume', 0)) if pd.notnull(curr.get('volume')) else 0.0
        vma20 = float(curr.get('Vol_SMA_20', c_vol)) if ("Vol_SMA_20" in sub_df.columns and pd.notnull(curr.get('Vol_SMA_20'))) else c_vol
        atr = float(curr.get('ATR', c_high - c_low)) if ("ATR" in sub_df.columns and pd.notnull(curr.get('ATR'))) else (c_high - c_low)

        c_body = abs(c_close - c_open)
        c_range = c_high - c_low + 1e-9
        p_body = abs(p_close - p_open)
        p_range = p_high - p_low + 1e-9
        c_is_green = c_close > c_open
        p_is_green = p_close > p_open

        lower_shadow = min(c_open, c_close) - c_low
        upper_shadow = c_high - max(c_open, c_close)
        
        # Trend / Swing Context
        recent_low = sub_df['low'].iloc[max(0, i-6):i].min()
        recent_high = sub_df['high'].iloc[max(0, i-6):i].max()
        is_at_dip = c_low <= recent_low * 1.015
        is_at_peak = c_high >= recent_high * 0.985

        # 1. Bullish Engulfing
        if not p_is_green and c_is_green and c_open <= p_close + 0.05 * p_body and c_close >= p_open - 0.05 * p_body and c_body > p_body and p_body >= 0.2 * p_range and is_at_dip:
            results.append({
                'name': 'Bullish Engulfing',
                'type': 'Candlestick Pattern',
                'bias': 'Bullish',
                'date': date,
                'price': c_close,
                'y_anchor': c_low,
                'arrow_side': 'bottom',
                'color': '#10b981',
                'description': 'Green candle engulfed previous red body at support (Strong buying pressure).'
            })

        # 2. Bearish Engulfing
        elif p_is_green and not c_is_green and c_open >= p_close - 0.05 * p_body and c_close <= p_open + 0.05 * p_body and c_body > p_body and p_body >= 0.2 * p_range and is_at_peak:
            results.append({
                'name': 'Bearish Engulfing',
                'type': 'Candlestick Pattern',
                'bias': 'Bearish',
                'date': date,
                'price': c_close,
                'y_anchor': c_high,
                'arrow_side': 'top',
                'color': '#ef4444',
                'description': 'Red candle engulfed previous green body at resistance (Strong selling rejection).'
            })

        # 3. Hammer (Bullish Pinbar)
        elif lower_shadow >= 2.0 * c_body and upper_shadow <= (0.25 * c_body + 0.05 * c_range) and is_at_dip:
            results.append({
                'name': 'Hammer (Pinbar)',
                'type': 'Candlestick Pattern',
                'bias': 'Bullish',
                'date': date,
                'price': c_close,
                'y_anchor': c_low,
                'arrow_side': 'bottom',
                'color': '#10b981',
                'description': f'Long lower shadow rejecting low at Tk {c_low:.1f}.'
            })

        # 4. Inverted Hammer (Bullish Reversal)
        elif upper_shadow >= 2.0 * c_body and lower_shadow <= (0.25 * c_body + 0.05 * c_range) and is_at_dip:
            results.append({
                'name': 'Inverted Hammer',
                'type': 'Candlestick Pattern',
                'bias': 'Bullish',
                'date': date,
                'price': c_close,
                'y_anchor': c_low,
                'arrow_side': 'bottom',
                'color': '#10b981',
                'description': f'Bullish test of overhead liquidity rejecting low at Tk {c_low:.1f}.'
            })

        # 5. Shooting Star (Bearish Pinbar)
        elif upper_shadow >= 2.0 * c_body and lower_shadow <= (0.25 * c_body + 0.05 * c_range) and is_at_peak:
            results.append({
                'name': 'Shooting Star',
                'type': 'Candlestick Pattern',
                'bias': 'Bearish',
                'date': date,
                'price': c_close,
                'y_anchor': c_high,
                'arrow_side': 'top',
                'color': '#ef4444',
                'description': f'Long upper wick rejecting peak high at Tk {c_high:.1f}.'
            })

        # 6. Hanging Man (Bearish Reversal)
        elif lower_shadow >= 2.0 * c_body and upper_shadow <= (0.25 * c_body + 0.05 * c_range) and is_at_peak:
            results.append({
                'name': 'Hanging Man',
                'type': 'Candlestick Pattern',
                'bias': 'Bearish',
                'date': date,
                'price': c_close,
                'y_anchor': c_high,
                'arrow_side': 'top',
                'color': '#ef4444',
                'description': f'Exhaustion hanging man at peak high Tk {c_high:.1f}.'
            })

        # 7. Piercing Line (Bullish Reversal)
        elif not p_is_green and p_body >= 0.35 * p_range and c_is_green and c_open <= p_close and c_close >= p_close + 0.5 * p_body and c_close < p_open and is_at_dip:
            results.append({
                'name': 'Piercing Line',
                'type': 'Candlestick Pattern',
                'bias': 'Bullish',
                'date': date,
                'price': c_close,
                'y_anchor': c_low,
                'arrow_side': 'bottom',
                'color': '#10b981',
                'description': 'Bullish piercing line closing over 50% into prior red candle body.'
            })

        # 8. Dark Cloud Cover (Bearish Reversal)
        elif p_is_green and p_body >= 0.35 * p_range and not c_is_green and c_open >= p_close and c_close <= p_close - 0.5 * p_body and c_close > p_open and is_at_peak:
            results.append({
                'name': 'Dark Cloud Cover',
                'type': 'Candlestick Pattern',
                'bias': 'Bearish',
                'date': date,
                'price': c_close,
                'y_anchor': c_high,
                'arrow_side': 'top',
                'color': '#ef4444',
                'description': 'Dark cloud cover penetrating over 50% into prior green candle body.'
            })

        # 9. Bullish Harami
        elif not p_is_green and c_is_green and c_open >= p_close and c_close <= p_open and c_body <= 0.65 * p_body and is_at_dip:
            results.append({
                'name': 'Bullish Harami',
                'type': 'Candlestick Pattern',
                'bias': 'Bullish',
                'date': date,
                'price': c_close,
                'y_anchor': c_low,
                'arrow_side': 'bottom',
                'color': '#10b981',
                'description': 'Inside green bar within prior red candle (Selling exhaustion).'
            })

        # 10. Bearish Harami
        elif p_is_green and not c_is_green and c_open <= p_close and c_close >= p_open and c_body <= 0.65 * p_body and is_at_peak:
            results.append({
                'name': 'Bearish Harami',
                'type': 'Candlestick Pattern',
                'bias': 'Bearish',
                'date': date,
                'price': c_close,
                'y_anchor': c_high,
                'arrow_side': 'top',
                'color': '#ef4444',
                'description': 'Inside red bar within prior green candle (Buying exhaustion).'
            })

        # 11. Dragonfly Doji (Bullish Reversal at Support)
        elif c_body / c_range <= 0.08 and lower_shadow >= 0.65 * c_range and is_at_dip:
            results.append({
                'name': 'Dragonfly Doji',
                'type': 'Candlestick Pattern',
                'bias': 'Bullish',
                'date': date,
                'price': c_close,
                'y_anchor': c_low,
                'arrow_side': 'bottom',
                'color': '#10b981',
                'description': f'Bullish Dragonfly Doji rejecting bottom support at Tk {c_low:.1f}.'
            })

        # 12. Gravestone Doji (Bearish Reversal at Resistance)
        elif c_body / c_range <= 0.08 and upper_shadow >= 0.65 * c_range and is_at_peak:
            results.append({
                'name': 'Gravestone Doji',
                'type': 'Candlestick Pattern',
                'bias': 'Bearish',
                'date': date,
                'price': c_close,
                'y_anchor': c_high,
                'arrow_side': 'top',
                'color': '#ef4444',
                'description': f'Bearish Gravestone Doji rejecting overhead resistance at Tk {c_high:.1f}.'
            })

        # 13. Regular Doji
        elif c_body / c_range <= 0.08 and c_range >= 0.005 * c_close:
            results.append({
                'name': 'Doji Candle',
                'type': 'Candlestick Pattern',
                'bias': 'Neutral',
                'date': date,
                'price': c_close,
                'y_anchor': c_high,
                'arrow_side': 'top',
                'color': '#8b5cf6',
                'description': 'Market equilibrium / indecision candle at turning point.'
            })

        # 14. 3-Bar Patterns (Morning Star / Evening Star / Three Soldiers / Three Crows)
        if i >= 2:
            prev2 = sub_df.iloc[i-2]
            p2_open, p2_close, p2_high, p2_low = float(prev2['open']), float(prev2['close']), float(prev2['high']), float(prev2['low'])
            p2_body = abs(p2_close - p2_open)
            p2_is_green = p2_close > p2_open
            
            # Morning Star
            if not p2_is_green and p2_body >= 0.4 * (p2_high - p2_low) and p_body <= 0.45 * p2_body and c_is_green and c_close >= p2_close + 0.5 * (p2_open - p2_close):
                results.append({
                    'name': 'Morning Star',
                    'type': 'Candlestick Pattern',
                    'bias': 'Bullish',
                    'date': date,
                    'price': c_close,
                    'y_anchor': c_low,
                    'arrow_side': 'bottom',
                    'color': '#10b981',
                    'description': '3-candle bullish reversal pattern signaling strong bottom turnaround.'
                })

            # Evening Star
            elif p2_is_green and p2_body >= 0.4 * (p2_high - p2_low) and p_body <= 0.45 * p2_body and not c_is_green and c_close <= p2_open + 0.5 * (p2_close - p2_open):
                results.append({
                    'name': 'Evening Star',
                    'type': 'Candlestick Pattern',
                    'bias': 'Bearish',
                    'date': date,
                    'price': c_close,
                    'y_anchor': c_high,
                    'arrow_side': 'top',
                    'color': '#ef4444',
                    'description': '3-candle bearish reversal pattern signaling top exhaustion.'
                })

            # Three White Soldiers
            elif p2_is_green and p_is_green and c_is_green and p2_body >= 0.4 * (p2_high - p2_low) and p_body >= 0.4 * p_range and c_body >= 0.4 * c_range and c_close > p_close > p2_close:
                results.append({
                    'name': 'Three White Soldiers',
                    'type': 'Candlestick Pattern',
                    'bias': 'Bullish',
                    'date': date,
                    'price': c_close,
                    'y_anchor': c_low,
                    'arrow_side': 'bottom',
                    'color': '#10b981',
                    'description': '3 consecutive strong green bars with rising closes (Powerful bullish thrust).'
                })

            # Three Black Crows
            elif not p2_is_green and not p_is_green and not c_is_green and p2_body >= 0.4 * (p2_high - p2_low) and p_body >= 0.4 * p_range and c_body >= 0.4 * c_range and c_close < p_close < p2_close:
                results.append({
                    'name': 'Three Black Crows',
                    'type': 'Candlestick Pattern',
                    'bias': 'Bearish',
                    'date': date,
                    'price': c_close,
                    'y_anchor': c_high,
                    'arrow_side': 'top',
                    'color': '#ef4444',
                    'description': '3 consecutive strong red bars with declining closes (Heavy institutional selling).'
                })

    return results

# Test on 3 stocks
for s in ['GP', 'SQURPHARMA', 'BRACBANK']:
    df = fetch_stocknow_1d(s)
    pats = detect_candlestick_patterns_history(df)
    print(f"{s}: {len(pats)} accurate patterns identified in last 60 days.")
    for p in pats[-4:]:
        print(f"  {p['date'].strftime('%Y-%m-%d')} -> {p['name']} ({p['bias']})")
