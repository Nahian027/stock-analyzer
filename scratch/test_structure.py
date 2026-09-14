import requests, json, datetime as dt, urllib3
urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://stocknow.com.bd/'
}

url = "https://stocknow.com.bd/api/v1/instruments/GP/history?data2=true&resolution=1D"
r = requests.get(url, headers=headers, verify=False)
data = r.json()

print(f"Data array length: {len(data)}")
for i, arr in enumerate(data):
    print(f"Array {i} len: {len(arr)}, min: {min(arr)}, max: {max(arr)}, last 3: {arr[-3:]}")

# Convert timestamps if one is timestamp
for i, arr in enumerate(data):
    if arr[-1] > 1000000000: # unix timestamp
        print(f"Array {i} is Timestamp! Date of last item: {dt.datetime.fromtimestamp(arr[-1])}")
