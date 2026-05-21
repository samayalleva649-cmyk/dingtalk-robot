import os, time, hmac, hashlib, base64, urllib.parse
from datetime import datetime, timedelta
import requests, pytz

def generate_signed_url(access_token, secret):
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(secret.encode(), string_to_sign.encode(), hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return f"https://oapi.dingtalk.com/robot/send?access_token={access_token}&timestamp={timestamp}&sign={sign}"

def send_dingtalk_message(webhook_url, content):
    r = requests.post(webhook_url, json={"msgtype":"markdown","markdown":{"title":"📊 流量高峰提醒","text":content}}, timeout=10)
    print("✅ 成功" if r.json().get("errcode")==0 else f"❌ 失败 {r.json()}")

regions = [
    ("德国","Europe/Berlin"), ("美国东部","US/Eastern"), ("美国西部","US/Pacific"),
    ("英国","Europe/London"), ("法国","Europe/Paris"), ("澳大利亚","Australia/Sydney"),
    ("奥地利","Europe/Vienna"), ("瑞士","Europe/Zurich"), ("希腊","Europe/Athens"),
    ("匈牙利","Europe/Budapest"), ("波兰","Europe/Warsaw"), ("捷克","Europe/Prague"),
    ("比利时","Europe/Brussels"), ("荷兰","Europe/Amsterdam"), ("西班牙","Europe/Madrid"),
    ("墨西哥","America/Mexico_City"), ("加拿大","America/Toronto")
]
peak_config = {name:{"hour":20,"minute":0} for name,_ in regions}
peak_config["美国东部"] = peak_config["美国西部"] = {"hour":21,"minute":0}
peak_config["澳大利亚"] = {"hour":19,"minute":0}
peak_config["希腊"] = peak_config["西班牙"] = peak_config["加拿大"] = {"hour":21,"minute":0}

def should_remind(peak_hour, peak_minute):
    now = datetime.now()
    target = now.replace(hour=peak_hour, minute=peak_minute, second=0, microsecond=0)
    if target <= now: target += timedelta(days=1)
    remind_time = target - timedelta(hours=1)
    return remind_time <= now < target

def get_message():
    beijing = datetime.now(pytz.timezone("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")
    lines = [f"## 📡 欧美流量高峰提醒\n### 📅 中国时间：{beijing}\n---\n| 地区 | 当地时间 | 高峰 | 提醒 |\n|------|----------|------|------|"]
    reminders = []
    for name, tz_str in regions:
        local = datetime.now(pytz.timezone(tz_str))
        peak = peak_config[name]
        peak_today = local.replace(hour=peak["hour"], minute=peak["minute"], second=0)
        if local >= peak_today: peak_today += timedelta(days=1)
        remain = peak_today - local
        hours, minutes = divmod(int(remain.total_seconds()), 3600)
        minutes //= 60
        if should_remind(peak["hour"], peak["minute"]):
            remind_text = f"🔔 **{hours}h{minutes}m**" if hours>0 else f"🟢 **{minutes}分钟后**"
            reminders.append(name)
        else:
            remind_text = f"{hours}h{minutes}m"
        lines.append(f"| {name} | {local.strftime('%H:%M:%S')} | {peak['hour']:02d}:{peak['minute']:02d} | {remind_text} |")
    lines.append(f"\n💡 提醒窗口：{', '.join(reminders)} 已进入高峰前1小时")
    return "\n".join(lines)

def main():
    token = os.getenv("DINGTALK_ACCESS_TOKEN")
    secret = os.getenv("DINGTALK_SECRET")
    if not token or not secret:
        print("❌ 缺少环境变量 DINGTALK_ACCESS_TOKEN / DINGTALK_SECRET")
        return
    url = generate_signed_url(token, secret)
    send_dingtalk_message(url, get_message())

if __name__ == "__main__":
    main()