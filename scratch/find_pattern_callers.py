with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if any(k in l for k in ['detect_candlestick', 'detect_chart_patterns', 'candle_patterns', 'candlestick', 'build_pattern_chart']):
        print(f"{i+1}: {l.strip()[:100]}")
