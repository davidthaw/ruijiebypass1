#!/usr/bin/env python3
"""
Ruijie Portal URL Grabber for Termux
ဒီ script က သင် Wi-Fi ချိတ်ထားစဉ် လက်ရှိ Gateway ကို ရှာပြီး
Portal URL အပြည့်ကို ထုတ်ပေးပါတယ်။
"""

import re
import requests
import subprocess
import sys
from urllib.parse import urlparse, parse_qs, urlunparse

# ------------------------------------------------------------
# 1. Gateway IP ရှာခြင်း (Termux, Linux, Android)
# ------------------------------------------------------------
def get_gateway():
    try:
        # Termux / Linux: ip route
        result = subprocess.run(["ip", "route", "show", "default"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if "default via" in line:
                parts = line.split()
                return parts[2]  # gateway IP
    except:
        pass
    try:
        # Android /proc/net/route
        with open("/proc/net/route", "r") as f:
            for line in f:
                parts = line.strip().split()
                if parts[1] == "00000000":  # default route
                    gw_hex = parts[2]
                    gw_ip = ".".join(str(int(gw_hex[i:i+2], 16)) for i in range(0, 8, 2)[::-1])
                    return gw_ip
    except:
        pass
    # Fallback
    return "192.168.1.1"

# ------------------------------------------------------------
# 2. Captive Portal Detection URL ကို သုံးပြီး Portal URL ထုတ်ခြင်း
# ------------------------------------------------------------
def get_portal_url_from_redirect(gateway):
    # Common captive portal detection endpoints
    test_urls = [
        "http://www.msftncsi.com/ncsi.txt",
        "http://captive.apple.com/hotspot-detect.html",
        "http://connectivitycheck.android.com/generate_204",
        f"http://{gateway}/"
    ]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for url in test_urls:
        try:
            # Do not follow redirects, capture Location header
            resp = requests.get(url, headers=headers, timeout=10, allow_redirects=False)
            if resp.status_code in (301, 302, 303, 307):
                location = resp.headers.get("Location")
                if location and "ruijienetworks.com" in location:
                    return location
            # Some portals embed portal URL in HTML meta refresh
            if "text/html" in resp.headers.get("Content-Type", ""):
                match = re.search(r'<meta[^>]+http-equiv=["\']refresh["\'][^>]+content=["\'][^;]+;url=([^"\']+)', resp.text, re.I)
                if match:
                    portal_url = match.group(1)
                    if "ruijienetworks.com" in portal_url:
                        return portal_url
        except Exception as e:
            continue
    return None

# ------------------------------------------------------------
# 3. မရသေးရင် Gateway ကို တိုက်ရိုက်သွားပြီး Form Action ထုတ်ခြင်း
# ------------------------------------------------------------
def get_portal_url_from_gateway_form(gateway):
    try:
        url = f"http://{gateway}/"
        resp = requests.get(url, timeout=10)
        # Find action="..." in form
        match = re.search(r'<form[^>]+action=["\']([^"\']+)["\']', resp.text, re.I)
        if match:
            action = match.group(1)
            if action.startswith("http"):
                return action
            elif action.startswith("/"):
                return f"http://{gateway}{action}"
    except:
        pass
    return None

# ------------------------------------------------------------
# 4. Main
# ------------------------------------------------------------
def main():
    print("[*] Scanning for gateway...")
    gateway = get_gateway()
    print(f"[+] Gateway IP: {gateway}")
    
    print("[*] Trying to capture portal URL (may take 10 sec)...")
    portal_url = get_portal_url_from_redirect(gateway)
    if not portal_url:
        portal_url = get_portal_url_from_gateway_form(gateway)
    
    if portal_url:
        print("\n" + "="*60)
        print("[✓] PORTAL URL FOUND:")
        print(portal_url)
        print("="*60)
        # Base64 encoding (like in screenshot)
        import base64
        b64 = base64.b64encode(portal_url.encode()).decode()
        print("\n[Base64 encoded (for easy copy)]:")
        print(b64)
        print("\n➡️  Copy the above URL and use in your bot: /input <URL>")
    else:
        print("[!] Could not fetch portal URL automatically.")
        print("[!] Please open browser and copy URL from address bar manually.")

if __name__ == "__main__":
    main()