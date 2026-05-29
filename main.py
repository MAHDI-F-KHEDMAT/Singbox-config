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
    "https://raw.githubusercontent.com/gfpcom/free-proxy-list/refs/heads/main/list/vless.txt"
]

async def fetch_source(session, url):
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 200: return await response.text()
    except Exception: pass
    return ""

def extract_vless_links(raw_content):
    if not raw_content: return []
    text = raw_content.strip()
    if "vless://" not in text:
        try:
            cleaned_text = re.sub(r'\s+', '', text)
            text = base64.b64decode(cleaned_text).decode('utf-8', errors='ignore')
        except Exception: pass
    links = re.findall(r'(vless://[^\s"\']+)', text)
    return [unquote(link.strip()) for link in links]

def parse_vless_link(link):
    try:
        parsed = urlparse(link)
        if parsed.scheme != 'vless': return None
        remark = unquote(parsed.fragment) if parsed.fragment else "Xray_Server"
        netloc = parsed.netloc
        if '@' not in netloc: return None
        uuid, server_port = netloc.split('@', 1)
        if ':' not in server_port: return None
        server, port = server_port.split(':', 1)
        
        query_params = parse_qs(parsed.query)
        params = {k: v[0] for k, v in query_params.items()}
        security = params.get('security', '').lower()
        
        if security not in ['reality', 'tls']: return None
            
        outbound = {
            "protocol": "vless",
            "settings": {
                "vnext": [{
                    "address": server,
                    "port": int(port),
                    "users": [{"id": uuid, "encryption": "none"}]
                }]
            },
            "streamSettings": {
                "network": params.get('type', 'tcp').lower(),
                "security": security
            },
            "tag": "proxy"
        }
        
        if 'flow' in params and params['flow']:
            outbound["settings"]["vnext"][0]["users"][0]["flow"] = params['flow']
            
        sni = params.get('sni', params.get('peer', ''))
        fp = params.get('fp', 'chrome')
        
        if security == 'reality':
            pbk = params.get('pbk', '')
            if not pbk: return None
            outbound["streamSettings"]["realitySettings"] = {
                "show": False, "fingerprint": fp, "serverName": sni, "publicKey": pbk, "shortId": params.get('sid', '')
            }
        elif security == 'tls':
            outbound["streamSettings"]["tlsSettings"] = {"serverName": sni, "fingerprint": fp}
            
        transport_type = outbound["streamSettings"]["network"]
        if transport_type == 'ws':
            outbound["streamSettings"]["wsSettings"] = {
                "path": params.get('path', '/'),
                "headers": {"Host": params['host']} if 'host' in params else {}
            }
        elif transport_type == 'grpc':
            outbound["streamSettings"]["grpcSettings"] = {
                "serviceName": params.get('serviceName', params.get('path', ''))
            }
            
        return {"remark": remark, "xray_outbound": outbound, "raw_link": link, "server": server, "port": int(port)}
    except Exception: return None

def deduplicate_configs(configs):
    seen = set()
    unique_configs = []
    for cfg in configs:
        unique_key = f"{cfg['server']}:{cfg['port']}"
        if unique_key not in seen:
            seen.add(unique_key)
            unique_configs.append(cfg)
    return unique_configs

def create_xray_config(outbound_details, local_port):
    return {
        "log": {"loglevel": "none"},
        "inbounds": [{
            "port": local_port, "listen": "127.0.0.1", "protocol": "socks", "settings": {"auth": "noauth", "udp": True}
        }],
        "outbounds": [outbound_details, {"protocol": "freedom", "tag": "direct"}]
    }

# --- تست سریع مرحله اول ---
async def test_quick_alive(config, port_queue, semaphore, tracker):
    async with semaphore:
        local_port = await port_queue.get()
        config_file = f"temp_quick_{local_port}.json"
        xr_config = create_xray_config(config['xray_outbound'], local_port)
        
        with open(config_file, 'w') as f: json.dump(xr_config, f)

        process = await asyncio.create_subprocess_exec(
            './xray', '-c', config_file, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )
        await asyncio.sleep(0.3)
        
        url = "http://cp.cloudflare.com/generate_204"
        connector = ProxyConnector.from_url(f"socks5://127.0.0.1:{local_port}")
        is_alive = False

        try:
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, timeout=3.0) as response:
                    if response.status in [200, 204]: is_alive = True
        except Exception: pass
        finally:
            try:
                process.terminate()
                await process.wait()
            except Exception: pass
            if os.path.exists(config_file): os.remove(config_file)
            await port_queue.put(local_port)

        tracker["done"] += 1
        if is_alive: tracker["alive"] += 1
        print(f"   📊 پیشرفت غربالگری اولیه Xray: {tracker['done']}/{tracker['total']} | زنده تا الان: {tracker['alive']}", end='\r', flush=True)
        return config if is_alive else None

# --- تست پایداری مرحله دوم ---
async def test_10s_stability(config, port_queue, semaphore, tracker):
    async with semaphore:
        local_port = await port_queue.get()
        config_file = f"temp_stable_{local_port}.json"
        xr_config = create_xray_config(config['xray_outbound'], local_port)
        
        with open(config_file, 'w') as f: json.dump(xr_config, f)

        process = await asyncio.create_subprocess_exec(
            './xray', '-c', config_file, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )
        await asyncio.sleep(0.4)
        
        url = "http://cp.cloudflare.com/generate_204"
        connector = ProxyConnector.from_url(f"socks5://127.0.0.1:{local_port}")
        
        success_checks = 0
        delays = []
        
        for i in range(5):
            start_time = time.perf_counter()
            try:
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get(url, timeout=2.0) as response:
                        if response.status in [200, 204]:
                            success_checks += 1
                            delays.append((time.perf_counter() - start_time) * 1000)
            except Exception: pass
            if i < 4: await asyncio.sleep(2.0)

        try:
            process.terminate()
            await process.wait()
        except Exception: pass
        if os.path.exists(config_file): os.remove(config_file)
        await port_queue.put(local_port)

        tracker["done"] += 1
        if success_checks == 5:
            tracker["stable"] += 1
            avg_delay = round(sum(delays) / 5, 2)
            print(f"   🧬 پیشرفت تست پایداری ۱۰ ثانیه‌ای: {tracker['done']}/{tracker['total']} | فوق پایدار نهایی: {tracker['stable']}", end='\r', flush=True)
            return {
                "remark": config['remark'], "xray_outbound": config['xray_outbound'], "raw_link": config['raw_link'],
                "stability": "100%", "avg_delay_ms": avg_delay
            }
        
        print(f"   🧬 پیشرفت تست پایداری ۱۰ ثانیه‌ای: {tracker['done']}/{tracker['total']} | فوق پایدار نهایی: {tracker['stable']}", end='\r', flush=True)
        return None

async def main():
    print("--- مرحله ۱: دانلود منابع کانفیگ رایگان ---")
    async with aiohttp.ClientSession() as session:
        fetch_tasks = [fetch_source(session, url) for url in SOURCES]
        raw_contents = await asyncio.gather(*fetch_tasks)

    print("\n--- مرحله ۲: استخراج لینک‌ها و حذف تکراری‌ها ---")
    all_raw_links = []
    for content in raw_contents: all_raw_links.extend(extract_vless_links(content))

    parsed_configs = []
    for link in all_raw_links:
        parsed = parse_vless_link(link)
        if parsed: parsed_configs.append(parsed)

    clean_configs = deduplicate_configs(parsed_configs)
    total_configs = len(clean_configs)
    print(f"📢 تعداد کل کانفیگ‌های منحصربه‌فرد برای شروع فرآیند: {total_configs}")

    if total_configs == 0:
        print("❌ هیچ کانفیگ معتبری پیدا نشد.")
        return

    max_concurrency = 40
    port_queue = asyncio.Queue()
    for p in range(10000, 10000 + max_concurrency): port_queue.put_nowait(p)
    sem = asyncio.Semaphore(max_concurrency)

    # 📌 شروع رسمی مرحله اول (Xray)
    print("\n⚡ [مرحله اول]: شروع تست سریع زنده بودن با هسته Xray...")
    quick_tracker = {"done": 0, "total": total_configs, "alive": 0}
    quick_tasks = [test_quick_alive(cfg, port_queue, sem, quick_tracker) for cfg in clean_configs]
    quick_results = await asyncio.gather(*quick_tasks)
    
    alive_first_stage = [res for res in quick_results if res is not None]
    total_alive = len(alive_first_stage)
    
    # 🎯 اینجا نتایج مرحله اول کاملاً مشخص و چاپ می‌شود
    print(f"\n\n🏁 نتایج مرحله اول مشخص شد:")
    print(f"   🔹 تعداد کل کانفیگ‌های اسکن شده: {total_configs}")
    print(f"   🔹 تعداد کانفیگ‌های زنده عبور کرده از فیلتر اول Xray: {total_alive}")

    if total_alive == 0:
        print("❌ متاسفانه هیچ کانفیگی از مرحله اول زنده بیرون نیامد. پایان عملیات.")
        return

    # 📌 شروع رسمی مرحله دوم (Stability)
    print(f"\n🚀 [مرحله دوم]: شروع تست قرنطینه ۱۰ ثانیه‌ای فقط برای {total_alive} کانفیگ زنده...")
    stable_sem = asyncio.Semaphore(15) 
    stable_tracker = {"done": 0, "total": total_alive, "stable": 0}
    stable_tasks = [test_10s_stability(cfg, port_queue, stable_sem, stable_tracker) for cfg in alive_first_stage]
    stable_results = await asyncio.gather(*stable_tasks)
    
    final_stable_configs = [res for res in stable_results if res is not None]
    final_stable_configs.sort(key=lambda x: x['avg_delay_ms'])

    print(f"\n\n🏁 نتایج نهایی تست پایداری مشخص شد:")
    print(f"   👑 تعداد کانفیگ‌های ۱۰۰٪ پایدار و بدون پکت‌لاست: {len(final_stable_configs)}")

    print("\n--- مرحله ۵: ذخیره‌سازی فایل‌های نهایی در ریپازیتوری ---")
    with open("sub.txt", "w", encoding="utf-8") as f:
        for cfg in final_stable_configs: f.write(cfg['raw_link'] + "\n")
            
    with open("valid_configs.json", "w", encoding="utf-8") as f:
        json.dump(final_stable_configs, f, indent=2, ensure_ascii=False)
        
    print(f"✅ فایل‌های sub.txt و valid_configs.json با موفقیت آپدیت شدند.")

if __name__ == "__main__":
    asyncio.run(main())
