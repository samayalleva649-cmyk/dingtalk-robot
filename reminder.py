import os
import time
import hmac
import hashlib
import base64
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
import json
from zoneinfo import ZoneInfo

def generate_signed_url(access_token, secret):
    timestamp = str(round(time.time() * 1000))
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(secret.encode(), string_to_sign.encode(), hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return f"https://oapi.dingtalk.com/robot/send?access_token={access_token}&timestamp={timestamp}&sign={sign}"

def send_dingtalk_message(webhook_url, content):
    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": "📊 流量高峰提醒",
            "text": content
        }
    }
    req = urllib.request.Request(webhook_url, data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            if result.get('errcode') == 0:
                print("✅ 消息发送成功")
            else:
                print(f"❌ 消息发送失败: {result}")
    except Exception as e:
        print(f"❌ 网络错误: {e}")

regions = [
    ("德国", "Europe/Berlin"),
    ("美国东部", "America/New_York"),
    ("美国西部", "America/Los_Angeles"),
    ("英国", "Europe/London"),
    ("法国", "Europe/Paris"),
    ("澳大利亚", "Australia/Sydney"),
    ("奥地利", "Europe/Vienna"),
    ("瑞士", "Europe/Zurich"),
    ("希腊", "Europe/Athens"),
    ("匈牙利", "Europe/Budapest"),
    ("波兰", "Europe/Warsaw"),
    ("捷克", "Europe/Prague"),
    ("比利时", "Europe/Brussels"),
    ("荷兰", "Europe/Amsterdam"),
    ("西班牙", "Europe/Madrid"),
    ("墨西哥", "America/Mexico_City"),
    ("加拿大", "America/Toronto"),
]

peak_hours = {
    "德国": 20, "美国东部": 21, "美国西部": 21, "英国": 20, "法国": 20,
    "澳大利亚": 19, "奥地利": 20, "瑞士": 20, "希腊": 21, "匈牙利": 20,
    "波兰": 20, "捷克": 20, "比利时": 20, "荷兰": 20, "西班牙": 21,
    "墨西哥": 20, "加拿大": 21,
}

def get_reminder_message():
    """返回需要提醒的地区信息，如果没有则不返回任何内容（返回None）"""
    beijing_now = datetime.now(ZoneInfo("Asia/Shanghai"))
    beijing_str = beijing_now.strftime("%Y-%m-%d %H:%M:%S")
    
    remind_list = []
    for name, tzname in regions:
        local_now = datetime.now(ZoneInfo(tzname))
        peak_hour = peak_hours[name]
        peak_today = local_now.replace(hour=peak_hour, minute=0, second=0, microsecond=0)
        if local_now >= peak_today:
            peak_today += timedelta(days=1)
        diff = peak_today - local_now
        # 提醒窗口：距离高峰 <= 1小时 且 还未到达高峰
        if 0 < diff.total_seconds() <= 3600:
            local_str = local_now.strftime("%Y-%m-%d %H:%M:%S")
            remind_list.append((name, local_str, peak_hour))
    
    if not remind_list:
        return None  # 没有需要提醒的地区，不发消息
    
    # 构建消息
    lines = [
        f"## 📡 流量高峰提醒（即将到来）",
        f"",
        f"### 📅 中国时间：{beijing_str}",
        f"---",
        f"| 🌍 地区 | 🕐 当地时间 | ⏰ 高峰时间 |",
        f"|--------|-----------|-----------|"
    ]
    for name, local_str, peak_hour in remind_list:
        lines.append(f"| {name} | {local_str} | {peak_hour:02d}:00 |")
    return "\n".join(lines)

def main():
    token = os.getenv("DINGTALK_ACCESS_TOKEN")
    secret = os.getenv("DINGTALK_SECRET")
    if not token or not secret:
        print("❌ 错误：未设置环境变量 DINGTALK_ACCESS_TOKEN 或 DINGTALK_SECRET")
        return
    content = get_reminder_message()
    if content is None:
        print("ℹ️ 当前没有国家进入高峰前1小时窗口，不发送消息")
        return
    url = generate_signed_url(token, secret)
    send_dingtalk_message(url, content)

if __name__ == "__main__":
    main()
