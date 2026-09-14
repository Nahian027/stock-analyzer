import requests, json, urllib3
urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://stocknow.com.bd/'
}

for sym in ['GP', 'SQURPHARMA', 'BRACBANK']:
    url = f"https://stocknow.com.bd/api/v1/instruments/{sym}/history?data2=true&resolution=1D"
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=5)
        print(f"=== {sym} -> Status {r.status_code} ===")
        if r.status_code == 200:
            data = r.json()
            print("Type of data:", type(data))
            if isinstance(data, dict):
                print("Keys:", data.keys())
                for k in ['t', 'o', 'h', 'l', 'c', 'v', 's']:
                    if k in data:
                        print(f"  {k} sample (len {len(data[k])}):", data[k][:5])
            elif isinstance(data, list):
                print("List len:", len(data), "Sample:", data[:2])
    except Exception as e:
        print("Error:", e)
