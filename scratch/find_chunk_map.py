import requests, re, urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}
url = "https://stocknow.com.bd/js/app.d312b277.js"
r = requests.get(url, headers=headers, verify=False)
text = r.text

# Extract chunk map: function(e){return"js/"+...}
chunk_func = re.findall(r'function\(e\)\{return"js/"\+.*?\}', text)
print("Chunk func:", chunk_func)

# Look for chart chunks
matches = re.findall(r'\{([0-9\:\,a-f\"\'\s]+)\}\[e\]', text)
for m in matches:
    print("Match map sample:", m[:150])

# Look for all mentions of endpoints: /charts, /candles, /history, /historical, /instruments
endpoints = set(re.findall(r'["\'](/[\w\-/]+)["\']', text))
print("Endpoints found:", [e for e in endpoints if any(k in e for k in ['chart', 'history', 'candle', 'trade', 'feed', 'stock', 'instrument', 'price'])])
