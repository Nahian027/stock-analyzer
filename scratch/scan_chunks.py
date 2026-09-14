import requests, re, urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}
url = "https://stocknow.com.bd/js/app.d312b277.js"
r = requests.get(url, headers=headers, verify=False)
text = r.text

pairs = re.findall(r'(\d+):"([a-f0-9]+)"', text)
print("Found chunk pairs:", len(pairs))

for cid, chash in pairs:
    chunk_url = f"https://stocknow.com.bd/js/{cid}.{chash}.js"
    try:
        rc = requests.get(chunk_url, headers=headers, verify=False, timeout=3)
        if rc.status_code == 200:
            if any(w in rc.text for w in ['historical', 'candles', 'history', 'tradingview', '1D', 'resolution', 'datafeed']):
                print(f"Match in {chunk_url}:")
                for m in re.findall(r'https?://[^\s"\'\<\>]+|/api/v1/[^\s"\'\<\>]+', rc.text):
                    print("   Found URL:", m)
                for line in rc.text.split(';'):
                    if any(w in line for w in ['/api/v1', 'history', 'candles', 'historical']):
                        print("   Line:", line[:120])
    except Exception as e:
        pass
