import requests, re, urllib3
urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://stocknow.com.bd/'
}

for js in ['/js/app.d312b277.js', '/js/chunk-vendors.00cab18c.js']:
    url = f"https://stocknow.com.bd{js}"
    r = requests.get(url, headers=headers, verify=False, timeout=10)
    print(f"=== {js} (len: {len(r.text)}) ===")
    
    # search for api, chart, history, instruments, candle, etc.
    matches = re.findall(r'api/v1/[a-zA-Z0-9_\-\/\?\&=\%]+', r.text)
    print("API matches:", set(matches))
    
    chart_matches = re.findall(r'[a-zA-Z0-9_\-\/]*chart[a-zA-Z0-9_\-\/]*', r.text, re.IGNORECASE)
    print("Chart matches:", set(chart_matches[:20]))

    history_matches = re.findall(r'[a-zA-Z0-9_\-\/]*history[a-zA-Z0-9_\-\/]*', r.text, re.IGNORECASE)
    print("History matches:", set(history_matches[:20]))
