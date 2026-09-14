import sys, requests, json, datetime as dt, urllib3
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}
url = "https://stocknow.com.bd/api/v1/instruments/GP/history?data2=true&resolution=1D"
r = requests.get(url, headers=headers, verify=False)
data = r.json()

r_inst = requests.get("https://stocknow.com.bd/api/v1/instruments", headers=headers, verify=False)
gp_quote = r_inst.json().get("GP", {})

print(f"Latest bar timestamp: {dt.datetime.fromtimestamp(data[5][-1])}")
print(f"Array 0 [-1]: {data[0][-1]}")
print(f"Array 1 [-1]: {data[1][-1]}")
print(f"Array 2 [-1]: {data[2][-1]}")
print(f"Array 3 [-1]: {data[3][-1]}")
print(f"Array 4 [-1]: {data[4][-1]}")

print(f"Quote Open: {gp_quote.get('open')}, Close/LTP: {gp_quote.get('close') or gp_quote.get('ltp')}, High: {gp_quote.get('high')}, Low: {gp_quote.get('low')}, Vol: {gp_quote.get('total_volume')}")
