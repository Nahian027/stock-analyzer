import requests, re, urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}
url = "https://stocknow.com.bd/js/app.d312b277.js"
r = requests.get(url, headers=headers, verify=False)
text = r.text

# Find occurrences of api/v1 and surrounding context
idx = 0
while True:
    pos = text.find('api/v1', idx)
    if pos == -1:
        break
    start = max(0, pos - 100)
    end = min(len(text), pos + 150)
    print(f"--- Context at {pos} ---")
    print(text[start:end])
    idx = pos + 6

# Also find chunk files loaded by webpack / vue router
chunks = re.findall(r'["\']js/([a-zA-Z0-9_\-\.]+)\.js["\']', text)
print("Chunks in app.js:", set(chunks))

# Also search for webpack chunk naming pattern
chunk_names = re.findall(r'(\d+):["\']([a-f0-9]+)["\']', text)
print("Webpack chunks count:", len(chunk_names))
