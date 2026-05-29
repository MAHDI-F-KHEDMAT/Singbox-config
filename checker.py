import asyncio
import json
import os
import time
import re
import base64
from urllib.parse import urlparse, parse_qs, unquote
import aiohttp
from aiohttp_socks import ProxyConnector

SOURCES = [
    "https://raw.githubusercontent.com/itsyebekhe/PSG/main/subscriptions/xray/base64/mix",
    "https://raw.githubusercontent.com/shaoyouvip/free/refs/heads/main/base64.txt",
    "https://raw.githubusercontent.com/telegeam/freenode/refs/heads/master/v2ray.txt",
    "https://raw.githubusercontent.com/DukeMehdi/FreeList-V2ray-Configs/refs/heads/main/Configs/VLESS-V2Ray-Configs-By-DukeMehdi.txt",
    "https://raw.githubusercontent.com/Flikify/Free-Node/refs/heads/main/v2ray.txt",
    "https://raw.githubusercontent.com/RaitonRed/ConfigsHub/refs/heads/main/Splitted-By-Protocol/vless.txt",
    "https://raw.githubusercontent.com/shuaidaoya/FreeNodes/refs/heads/main/nodes/base64.txt",
    "https://raw.githubusercontent.com/penhandev/AutoAiVPN/refs/heads/main/allConfigs.txt",
    "https://raw.githubusercontent.com/Firmfox/Proxify/refs/heads/main/v2ray_configs/seperated_by_protocol/vless.txt",
    "https://raw.githubusercontent.com/crackbest/V2ray-Config/refs/heads/main/config.txt",
    "https://raw.githubusercontent.com/kismetpro/NodeSuber/refs/heads/main/Splitted-By-Protocol/vless.txt",
    "https://raw.githubusercontent.com/jagger235711/V2rayCollector/refs/heads/main/results/vless.txt",
    "https://raw.githubusercontent.com/mohamadfg-dev/telegram-v2ray-configs-collector/refs/heads/main/category/vless.txt",
    "https://raw.githubusercontent.com/SoroushImanian/BlackKnight/refs/heads/main/sub/vless",
    "https://raw.githubusercontent.com/Matin-RK0/ConfigCollector/refs/heads/main/subscription.txt",
    "https://raw.githubusercontent.com/Argh73/VpnConfigCollector/refs/heads/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/3yed-61/configs-collector/refs/heads/main/classified_output/vless.txt",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/refs/heads/main/sub/share/vless",
    "https://raw.githubusercontent.com/ircfspace/XraySubRefiner/refs/heads/main/export/soliSpirit/normal",
    "https://raw.githubusercontent.com/ircfspace/XraySubRefiner/refs/heads/main/export/psgV6/normal",
    "https://raw.githubusercontent.com/ircfspace/XraySubRefiner/refs/heads/main/export/psgMix/normal",
    "https://raw.githubusercontent.com/MhdiTaheri/V2rayCollector_Py/refs/heads/main/sub/Mix/mix.txt",
    "https://raw.githubusercontent.com/T3stAcc/V2Ray/refs/heads/main/Splitted-By-Protocol/vless.txt",
    "https://raw.githubusercontent.com/F0rc3Run/F0rc3Run/refs/heads/main/splitted-by-protocol/vless.txt",
    "https://raw.githubusercontent.com/V2RayRoot/V2RayConfig/refs/heads/main/Config/vless.txt",
    "https://raw.githubusercontent.com/LalatinaHub/Mineral/refs/heads/master/result/nodes",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/refs/heads/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/hamedcode/port-based-v2ray-configs/refs/heads/main/sub/vless.txt",
    "https://raw.githubusercontent.com/iboxz/free-v2ray-collector/refs/heads/main/main/vless",
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/refs/heads/main/Splitted-By-Protocol/vless.txt",
    "https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/refs/heads/main/vless_configs.txt",
    "https://raw.githubusercontent.com/Pasimand/v2ray-config-agg/refs/heads/main/config.txt",
    "https://raw.githubusercontent.com/arshiacomplus/v2rayExtractor/refs/heads/main/vless.html",
    "https://raw.githubusercontent.com/xyfqzy/free-nodes/refs/heads/main/nodes/vless.txt",
    "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/14.txt",
    "https://raw.githubusercontent.com/Awmiroosen/awmirx-v2ray/refs/heads/main/blob/main/v2-sub.txt",
    "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/refs/heads/main/Protocols/vless.txt",
    "https://media.githubusercontent.com/media/gfpcom/free-proxy-list/refs/heads/main/list/vless.txt"
]

# ==================== ۱. دانلود و استخراج لینک‌ها ====================
async def fetch_source(session, url):
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                return await response.text()
    except Exception:
        pass
    return ""

def extract_vless_links(raw_content):
    if not raw_content:
        return []
    text = raw_content.strip()
    if "vless://" not in text:
        try:
            cleaned_text = re.sub(r'\s+', '', text)
            text = base64.b64decode(cleaned_text).decode('utf-8', errors='ignore')
        except Exception:
            pass
    links = re.findall(r'(vless://[^\s"\']+)', text)
    return [unquote(link.strip()) for link in links]

# ==================== ۲. پارسر و فیلتر (Reality / TLS) ====================
def parse_vless_link(link):
    try:
        parsed = urlparse(link)
        if parsed.scheme != 'vless':
            return None
        remark = unquote(parsed.fragment) if parsed.fragment else "VLESS_Server"
        netloc = parsed.netloc
        uuid, server_port = netloc.split('@', 1)
        server, port = server_port.split(':', 1)
        
        query_params = parse_qs(parsed.query)
        params = {k: v[0] for k, v in query_params.items()}
        security = params.get('security', '').lower()
        
        if security not in ['reality', 'tls']:
            return None
            
        outbound = {"type": "vless", "tag": "proxy", "server": server, "server_port": int(port), "uuid": uuid}
        if 'flow' in params: outbound['flow'] = params['flow']
        
        tls_config = {"enabled": True, "server_name": params.get('sni', params.get('peer', ''))}
        tls_config["utls"] = {"enabled": True, "fingerprint": params.get('fp', 'chrome')}
        
        if security == 'reality':
            tls_config['reality'] = {"enabled": True, "public_key": params.get('pbk', ''), "short_id": params.get('sid', '')}
        outbound['tls'] = tls_config
        
        transport_type = params.get('type', 'tcp').lower()
        if transport_type in ['ws', 'grpc']:
            transport = {"type": transport_type}
            if transport_type == 'ws':
                transport['path'] = params.get('path', '/')
                if 'host' in params: transport['headers'] = {"Host": params['host']}
            elif transport_type == 'grpc':
                transport['service_name'] = params.get('serviceName', params.get('path', ''))
            outbound['transport'] = transport
            
        return {"remark": remark, "singbox_outbound": outbound}
    except Exception:
        return None

# ==================== ۳. حذف تکراری‌ها ====================
def deduplicate_configs(configs):
    seen = set()
    unique_configs = []
    for cfg in configs:
        outbound = cfg.get('singbox_outbound', {})
        unique_key = f"{outbound.get('server')}:{outbound.get('port')}:{outbound.get('uuid', '')}"
        if unique_key not in seen:
            seen.add(unique_key)
            unique_configs.append(cfg)
    return unique_configs

# ==================== ۴. تست لایه ۷ با ابزار پیشرفت کار مانیتورینگ ====================
def create_singbox_config(outbound_details, local_port):
    return {
        "log": {"level": "silent"},
        "inbounds": [{"type": "socks", "listen": "127.0.0.1", "listen_port": local_port}],
        "outbounds": [outbound_details, {"type": "direct", "tag": "direct"}]
    }

async def test_l7_config(config, local_port, semaphore, tracker):
    """ تست لایه ۷ کانفیگ + آپدیت زنده درصد پیشرفت کار """
    async with semaphore:
        config_file = f"temp_config_{local_port}.json"
        sb_config = create_singbox_config(config['singbox_outbound'], local_port)
        
        with open(config_file, 'w') as f:
            json.dump(sb_config, f)

        process = await asyncio.create_subprocess_exec(
            './sing-box', 'run', '-c', config_file,
            stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )
        await asyncio.sleep(0.4)
        
        url = "http://cp.cloudflare.com/generate_204"
        connector = ProxyConnector.from_url(f"socks5://127.0.0.1:{local_port}")
        is_working = False
        real_delay = float('inf')
        start_time = time.perf_counter()

        try:
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, timeout=3.0) as response:
                    if response.status in [200, 204]:
                        is_working = True
                        real_delay = (time.perf_counter() - start_time) * 1000
        except Exception:
            pass
        finally:
            try:
                process.terminate()
                await process.wait()
            except Exception:
                pass
            if os.path.exists(config_file):
                os.remove(config_file)

        # 📊 آپدیت وضعیت ابزار مانیتورینگ پیشرفت
        tracker["done"] += 1
        if is_working:
            tracker["alive"] += 1
            
        percent = (tracker["done"] / tracker["total"]) * 100
        # نمایش لحظه‌ای درصد و وضعیت در ترمینال
        print(f"⏳ پیشرفت تست: {percent:.1f}% ({tracker['done']}/{tracker['total']}) | زنده تا این لحظه: {tracker['alive']}", end='\r', flush=True)

        return {
            "remark": config['remark'],
            "singbox_outbound": config['singbox_outbound'],
            "is_working": is_working,
            "real_delay": round(real_delay, 2) if is_working else "Timeout"
        }

# ==================== ۵. بدنه اصلی مدیریت فرآیند ====================
async def main():
    print("--- مرحله ۱: دانلود هم‌زمان منابع گیت‌هاب ---")
    start_fetch = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        fetch_tasks = [fetch_source(session, url) for url in SOURCES]
        raw_contents = await asyncio.gather(*fetch_tasks)
    print(f"دانلود منابع تمام شد. زمان واکشی: {time.perf_counter() - start_fetch:.2f} ثانیه")

    print("\n--- مرحله ۲: استخراج لینک‌ها و فیلتر کردن نوع امنیت (Reality/TLS) ---")
    all_raw_links = []
    for content in raw_contents:
        all_raw_links.extend(extract_vless_links(content))
    print(f"تعداد کل لینک‌های خام پیدا شده: {len(all_raw_links)}")

    parsed_configs = []
    for link in all_raw_links:
        parsed = parse_vless_link(link)
        if parsed:
            parsed_configs.append(parsed)
    print(f"تعداد کانفیگ‌های مجاز (فقط Reality و TLS): {len(parsed_configs)}")

    print("\n--- مرحله ۳: حذف کانفیگ‌های تکراری (Deduplication) ---")
    clean_configs = deduplicate_configs(parsed_configs)
    total_to_test = len(clean_configs)
    print(f"تعداد کانفیگ‌های یکتای نهایی برای ارسال به تست لایه ۷: {total_to_test}")

    if total_to_test == 0:
        print("کانفیگی برای تست موجود نیست.")
        return

    print("\n--- مرحله ۴: شروع تست پایداری لایه ۷ ---")
    max_concurrency = 30
    sem = asyncio.Semaphore(max_concurrency)
    
    # 🛠 ساخت دیکشنری مانیتورینگ برای پاس دادن به ورکرها
    progress_tracker = {
        "done": 0,
        "total": total_to_test,
        "alive": 0
    }
    
    start_test = time.perf_counter()
    test_tasks = []
    for idx, cfg in enumerate(clean_configs):
        assigned_port = 2000 + (idx % max_concurrency)
        # پاس دادن سیستم مانیتورینگ به تابع تست
        test_tasks.append(test_l7_config(cfg, assigned_port, sem, progress_tracker))

    results = await asyncio.gather(*test_tasks)
    
    # چاپ یک اینتر در پایان کار مانیتورینگ تا خط بعدی خراب نشود
    print("") 

    working_configs = [res for res in results if res['is_working']]
    working_configs.sort(key=lambda x: x['real_delay'])

    print(f"\n--- پایان کل فرآیند در {time.perf_counter() - start_test:.2f} ثانیه ---")
    print(f"تعداد کانفیگ‌های ۱۰۰٪ سالم و پرسرعت: {len(working_configs)}")

    with open("valid_configs.json", "w", encoding="utf-8") as f:
        json.dump(working_configs, f, indent=2, ensure_ascii=False)
    print("خروجی نهایی در فایل valid_configs.json ذخیره شد.")

if __name__ == "__main__":
    asyncio.run(main())
