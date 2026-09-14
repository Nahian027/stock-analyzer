import requests, re, urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}
url = "https://stocknow.com.bd/js/app.d312b277.js"
r = requests.get(url, headers=headers, verify=False)
text = r.text

# Find all string literals that look like paths or URLs
urls = re.findall(r'["\'](/[^"\']+)["\']', text)
print("Paths in app.js:")
for u in set(urls):
    if any(k in u for k in ['api', 'data', 'instrument', 'chart', 'candle', 'history', 'price', 'trade', 'feed', 'stock']):
        print('  ', u)

# Also check for env or base URL variables
base_urls = re.findall(r'https?://[^\s"\'\<\>]+', text)
print("Base URLs in app.js:", set(base_urls))

# Also search for tradingview or chart datafeed configuration
datafeeds = re.findall(r'[a-zA-Z0-9_\-\.\/]*datafeed[a-zA-Z0-9_\-\.\/]*', text, re.IGNORECASE)
print("Datafeeds:", set(datafeeds))
