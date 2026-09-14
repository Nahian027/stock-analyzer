import requests, json, re, urllib3
urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://stocknow.com.bd/',
    'Accept': 'application/json, text/plain, */*'
}

# Check stocknow company page or next.js / js files to find chart / history API
try:
    r = requests.get('https://stocknow.com.bd/company/GP', headers=headers, verify=False, timeout=6)
    print('Company page:', r.status_code)
    scripts = re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', r.text)
    print('Scripts found:', len(scripts))
    for s in scripts:
        print(' Script:', s)
        if '_app' in s or 'main' in s or 'company' in s or 'webpack' in s or 'index' in s or 'pages' in s:
            s_url = s if s.startswith('http') else f"https://stocknow.com.bd{s}"
            try:
                res_s = requests.get(s_url, headers=headers, verify=False, timeout=6)
                apis = set(re.findall(r'https?://[a-zA-Z0-9\.\_\:\-]+/api/v1/[a-zA-Z0-9\/\-\_\?\&=\%]+', res_s.text))
                api_paths = set(re.findall(r'["\'](/api/v1/[a-zA-Z0-9\/\-\_\?\&=\%]+)["\']', res_s.text))
                if apis or api_paths:
                    print(f'   APIs in {s}:', apis, api_paths)
            except Exception as ex:
                print('   Err fetching script:', ex)
except Exception as e:
    print('Error:', e)
