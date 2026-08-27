import requests
import re
import datetime as dt
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

today = dt.date.today()

def parse_date_obj(d_str: str):
    if not d_str or any(k in str(d_str).lower() for k in ['postponed', 'later', 'notice', 'tbd', 'permission', 'tba']):
        return None
    cleaned = re.sub(r'^[^\d]+', '', str(d_str)).strip()
    m1 = re.search(r'(\d{1,2})-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-(\d{2,4})', cleaned, re.IGNORECASE)
    if m1:
        day, mon, yr = int(m1.group(1)), m1.group(2).capitalize(), int(m1.group(3))
        if yr < 100:
            yr += 2000
        try:
            return dt.datetime.strptime(f'{day}-{mon}-{yr}', '%d-%b-%Y').date()
        except Exception:
            pass
    m2 = re.search(r'(\d{1,2})\s+([A-Za-z]+),?\s+(\d{4})', cleaned)
    if m2:
        day, mon, yr = int(m2.group(1)), m2.group(2)[:3].capitalize(), int(m2.group(3))
        try:
            return dt.datetime.strptime(f'{day}-{mon}-{yr}', '%d-%b-%Y').date()
        except Exception:
            pass
    m3 = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', cleaned)
    if m3:
        day, mon, yr = int(m3.group(1)), int(m3.group(2)), int(m3.group(3))
        try:
            return dt.date(yr, mon, day)
        except Exception:
            pass
    return None

seen = set()
rec_list = []

# Scan 30 pages of live news
for p in range(1, 35):
    try:
        url = f'https://stocknow.com.bd/api/v1/news?page={p}'
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=6)
        if res.status_code == 200:
            for item in res.json().get('data', []):
                code = str(item.get('prefix', '')).strip().upper()
                title = str(item.get('title') or '').strip()
                details = str(item.get('details', '')).strip()
                full_txt = f'{title} {details}'
                
                # Check for Record Date in any format (e.g. 27-Aug-2026, 27.08.2026, 06 September 2026, 03.09.2026)
                matches = re.findall(r'(?:[Rr]ecord\s+[Dd]ate|[Ss]uspended\s+on\s+record\s+date|[Ee]ntitlement\s+of\s+coupon)[^\.\;\n]{0,60}?(\d{1,2}-(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{2,4}|\d{1,2}\s+[A-Za-z]+,?\s+\d{4}|\d{1,2}\.\d{1,2}\.\d{4})', full_txt)
                for m in matches:
                    rdt = parse_date_obj(m)
                    if rdt and rdt >= today:
                        k = (code, str(rdt))
                        if k not in seen:
                            seen.add(k)
                            rec_list.append({
                                'code': code,
                                'rec_date': m,
                                'rec_dt': rdt,
                                'title': title or details[:80],
                                'details': details
                            })
    except Exception as e:
        pass

rec_list.sort(key=lambda x: x['rec_dt'])
print(f'Total Upcoming Record Dates found in 35 pages of DSE disclosures: {len(rec_list)}')
for i, r in enumerate(rec_list):
    days = (r['rec_dt'] - today).days
    print(f"{i+1:02d}. [{r['rec_dt']} - In {days} Days] {r['code']} --> Record Date: {r['rec_date']} | Title: {r['title'][:70]}")
