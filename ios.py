#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Turbo Network Engine v2 - iOS a-Shell Edition (No Key System)
"""

import requests
import re
import urllib3
import time
import threading
import logging
import random
import os
import sys
from urllib.parse import urlparse, parse_qs, urljoin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Colors
black = "\033[0;30m"
red = "\033[0;31m"
bred = "\033[1;31m"
green = "\033[0;32m"
bgreen = "\033[1;32m"
yellow = "\033[0;33m"
byellow = "\033[1;33m"
blue = "\033[0;34m"
bblue = "\033[1;34m"
purple = "\033[0;35m"
bpurple = "\033[1;35m"
cyan = "\033[0;36m"
bcyan = "\033[1;36m"
white = "\033[0;37m"
reset = "\033[00m"

# Config
PING_THREADS = 5
MIN_INTERVAL = 0.05
MAX_INTERVAL = 0.2
DEBUG = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%H:%M:%S"
)

stop_event = threading.Event()

def check_real_internet():
    try:
        return requests.get("http://www.google.com", timeout=3).status_code == 200
    except:
        return False

def banner():
    print(f"""{purple}
╔══════════════════════════════════════╗
║        TURBO NETWORK ENGINE v2      ║
║        iOS a-Shell Edition          ║
╚══════════════════════════════════════╝
{reset}""")

def high_speed_ping(auth_link, sid):
    session = requests.Session()
    ping_count = 0
    success_count = 0
    
    while not stop_event.is_set():
        try:
            start = time.time()
            r = session.get(auth_link, timeout=5)
            elapsed = (time.time() - start) * 1000
            ping_count += 1
            success_count += 1
            
            if elapsed < 50:
                color = green
            elif elapsed < 100:
                color = yellow
            else:
                color = red
            
            print(f"{color}[✓]{reset} SID {sid} | Ping: {elapsed:.1f}ms | Success: {success_count}/{ping_count}", end="\r")
            
        except requests.exceptions.Timeout:
            ping_count += 1
            print(f"{red}[X]{reset} SID {sid} | TIMEOUT | Success: {success_count}/{ping_count}", end="\r")
        except requests.exceptions.ConnectionError:
            ping_count += 1
            print(f"{red}[X]{reset} SID {sid} | Connection Lost | Success: {success_count}/{ping_count}", end="\r")
        except Exception as e:
            if DEBUG:
                print(f"{red}[!]{reset} Error: {e}", end="\r")
        
        time.sleep(random.uniform(MIN_INTERVAL, MAX_INTERVAL))

def start_process():
    os.system('clear' if os.name == 'posix' else 'cls')
    banner()
    logging.info(f"{cyan}Initializing Turbo Engine...{reset}")
    
    print(f"\n{cyan}[*] Network Status:{reset}")
    print(f"    Checking internet connectivity...")
    
    if check_real_internet():
        print(f"    {green}[✓] Internet is already active{reset}")
    
    print(f"\n{cyan}[*] Starting portal detection...{reset}")

    while not stop_event.is_set():
        session = requests.Session()
        # iOS အတွက် Apple captive portal detection URL
        test_url = "http://captive.apple.com"

        try:
            r = requests.get(test_url, allow_redirects=True, timeout=5)

            if r.url == test_url:
                if check_real_internet():
                    print(f"{yellow}[•]{reset} Internet Already Active... Waiting     ", end="\r")
                    time.sleep(5)
                    continue

            portal_url = r.url
            parsed_portal = urlparse(portal_url)
            portal_host = f"{parsed_portal.scheme}://{parsed_portal.netloc}"

            print(f"\n{cyan}[*] Captive Portal Detected: {portal_host}{reset}")

            r1 = session.get(portal_url, verify=False, timeout=10)
            path_match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", r1.text)
            next_url = urljoin(portal_url, path_match.group(1)) if path_match else portal_url
            r2 = session.get(next_url, verify=False, timeout=10)

            sid = parse_qs(urlparse(r2.url).query).get('sessionId', [None])[0]

            if not sid:
                sid_match = re.search(r'sessionId=([a-zA-Z0-9]+)', r2.text)
                sid = sid_match.group(1) if sid_match else None

            if not sid:
                logging.warning(f"{red}Session ID Not Found{reset}")
                time.sleep(5)
                continue

            print(f"{green}[✓]{reset} Session ID Captured: {sid}")

            print(f"{cyan}[*] Checking Voucher Endpoint...{reset}")
            voucher_api = f"{portal_host}/api/auth/voucher/"

            try:
                v_res = session.post(
                    voucher_api,
                    json={'accessCode': '123456', 'sessionId': sid, 'apiVersion': 1},
                    timeout=5
                )
                print(f"{green}[✓]{reset} Voucher API Status: {v_res.status_code}")
            except:
                print(f"{yellow}[!]{reset} Voucher Endpoint Skipped")

            params = parse_qs(parsed_portal.query)
            gw_addr = params.get('gw_address', ['192.168.60.1'])[0]
            gw_port = params.get('gw_port', ['2060'])[0]

            auth_link = f"http://{gw_addr}:{gw_port}/wifidog/auth?token={sid}&phonenumber=12345"

            print(f"{purple}[*] Launching {PING_THREADS} Turbo Threads...{reset}")
            print(f"{cyan}[*] Target: {gw_addr}:{gw_port}{reset}")
            print(f"{yellow}[!] Press Ctrl+C to stop{reset}\n")

            threads = []
            for i in range(PING_THREADS):
                t = threading.Thread(target=high_speed_ping, args=(auth_link, sid), daemon=True)
                t.start()
                threads.append(t)

            last_status = False
            while not stop_event.is_set():
                is_connected = check_real_internet()
                
                if is_connected and not last_status:
                    print(f"\n{green}[✓] Internet Connected!{reset}")
                elif not is_connected and last_status:
                    print(f"\n{red}[X] Internet Disconnected! Reconnecting...{reset}")
                
                last_status = is_connected
                time.sleep(2)

        except KeyboardInterrupt:
            raise
        except Exception as e:
            if DEBUG:
                logging.error(f"{red}Error: {e}{reset}")
            time.sleep(5)

if __name__ == "__main__":
    try:
        start_process()
    except KeyboardInterrupt:
        stop_event.set()
        print(f"\n{red}Turbo Engine Shutdown...{reset}")
