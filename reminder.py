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

def get_message():
    beijing_now = datetime.now(ZoneInfo("Asia/Shanghai"))
    beijing_str = beijing_now.strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"## 📡 欧美地区流量高峰提醒",
        f"",
        f"### 📅 中国时间（北京）：**{beijing_str}**",
        f"---",
        f"| 🌍 地区 | 🕐 当地时间 | ⏰ 高峰时间 | ⏱️ 剩余提醒 |",
        f"|--------|-----------|-----------|-----------|"
    ]
    reminders = []
    for name, tzname in regions:
        local_now = datetime.now(ZoneInfo(tzname))
        local_str = local_now.strftime("%Y-%m-%d %H:%M:%S")
        peak_hour = peak_hours[name]
        peak_today = local_now.replace(hour=peak_hour, minute=0, second=0, microsecond=0)
        if local_now >= peak_today:
            peak_today += timedelta(days=1)
        diff = peak_today - local_now
        hours_left = diff.seconds // 3600
        minutes_left = (diff.seconds % 3600) // 60
        if diff.days == 0 and hours_left < 1:
            remain_msg = f"🟢 **{minutes_left}分钟后** 高峰即将到来"
            reminders.append(name)
        elif diff.days == 0 and hours_left < 24:
            remain_msg = f"🔔 **{hours_left}h{minutes_left}m**"
            reminders.append(name)
        else:
            remain_msg = f"{hours_left}h{minutes_left}m"
        lines.append(f"| {name} | {local_str} | {peak_hour:02d}:00 | {remain_msg} |")
    lines.append("")
    lines.append("### 💡 说明")
    lines.append(f"- 已进入提醒窗口：{', '.join(reminders) if reminders else '无'}")
    lines.append("- 提醒窗口为高峰前1小时，请提前准备")
    return "\n".join(lines)

def main():
    token = os.getenv("DINGTALK_ACCESS_TOKEN")
    secret = os.getenv("DINGTALK_SECRET")
    if not token or not secret:
        print("❌ 错误：未设置环境变量 DINGTALK_ACCESS_TOKEN 或 DINGTALK_SECRET")
        return
    url = generate_signed_url(token, secret)
    content = get_message()
    send_dingtalk_message(url, content)

if __name__ == "__main__":
    main()
