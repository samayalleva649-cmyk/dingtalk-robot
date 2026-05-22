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

# ==================== 钉钉签名与发送 ====================
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

# ==================== 地区配置 ====================
# 提醒窗口（秒）—— 1小时 = 3600秒
REMIND_WINDOW_SECONDS = 3600

# 各国家/地区配置： (显示名称, 时区ID, 高峰时段列表)
# 高峰时段格式：(小时, 分钟, 描述)
regions = [
    # 北美
    ("美国东部", "America/New_York", [(7,0,"早高峰"), (12,0,"午高峰"), (19,0,"晚高峰")]),
    ("美国西部", "America/Los_Angeles", [(7,0,"早高峰"), (12,0,"午高峰"), (19,0,"晚高峰")]),
    ("加拿大", "America/Toronto", [(7,0,"早高峰"), (12,0,"午高峰"), (19,0,"晚高峰")]),
    ("墨西哥", "America/Mexico_City", [(9,0,"早高峰"), (14,0,"午高峰"), (20,0,"晚高峰")]),
    # 英国及西欧核心市场
    ("英国", "Europe/London", [(12,0,"午高峰"), (18,0,"晚高峰")]),                          # 无显著早高峰，午12-15/晚18-22
    ("德国", "Europe/Berlin", [(12,0,"午高峰"), (19,0,"晚高峰")]),                          # 晚19-23为主力，午12-14次高峰
    ("法国", "Europe/Paris", [(12,0,"午高峰"), (19,0,"晚高峰")]),                            # 晚19-23黄金期，午12-14次高峰
    ("奥地利", "Europe/Vienna", [(12,0,"午高峰"), (19,0,"晚高峰")]),
    ("瑞士", "Europe/Zurich", [(12,0,"午高峰"), (19,0,"晚高峰")]),
    ("希腊", "Europe/Athens", [(12,0,"午高峰"), (19,0,"晚高峰")]),
    ("匈牙利", "Europe/Budapest", [(12,0,"午高峰"), (19,0,"晚高峰")]),
    ("波兰", "Europe/Warsaw", [(12,0,"午高峰"), (19,0,"晚高峰")]),
    ("捷克", "Europe/Prague", [(12,0,"午高峰"), (19,0,"晚高峰")]),
    ("比利时", "Europe/Brussels", [(12,0,"午高峰"), (19,0,"晚高峰")]),
    ("荷兰", "Europe/Amsterdam", [(12,0,"午高峰"), (19,0,"晚高峰")]),
    ("西班牙", "Europe/Madrid", [(14,0,"午高峰"), (21,0,"晚高峰")]),                         # 午高峰晚2小时，晚高峰也相应延迟
    # 大洋洲
    ("澳大利亚", "Australia/Sydney", [(7,0,"早高峰"), (12,0,"午高峰"), (18,0,"晚高峰")]),    # 早7-11/午12-14/晚18-22
]

def get_reminder_message():
    """返回需要提醒的地区信息，无提醒则返回None"""
    beijing_now = datetime.now(ZoneInfo("Asia/Shanghai"))
    beijing_str = beijing_now.strftime("%Y-%m-%d %H:%M:%S")
    
    remind_list = []
    for name, tzname, peaks in regions:
        local_now = datetime.now(ZoneInfo(tzname))
        local_str = local_now.strftime("%Y-%m-%d %H:%M:%S")
        
        for hour, minute, desc in peaks:
            peak_dt = local_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if local_now >= peak_dt:
                peak_dt += timedelta(days=1)
            delta_seconds = (peak_dt - local_now).total_seconds()
            if 0 < delta_seconds <= REMIND_WINDOW_SECONDS:
                remind_list.append((name, local_str, desc, f"{hour:02d}:{minute:02d}"))
                break  # 一个地区只提醒一次（距离最近的高峰）
    
    if not remind_list:
        return None
    
    lines = [
        f"## 📡 流量高峰提醒（即将到来）",
        f"",
        f"### 📅 中国时间：{beijing_str}",
        f"---",
        f"| 🌍 地区 | 🕐 当地时间 | ⏰ 即将到来的高峰 |",
        f"|--------|-----------|----------------|"
    ]
    for name, local_str, desc, peak_time in remind_list:
        lines.append(f"| {name} | {local_str} | {desc} {peak_time} |")
    return "\n".join(lines)

def main():
    token = os.getenv("DINGTALK_ACCESS_TOKEN")
    secret = os.getenv("DINGTALK_SECRET")
    if not token or not secret:
        print("❌ 错误：未设置环境变量 DINGTALK_ACCESS_TOKEN 或 DINGTALK_SECRET")
        return
    content = get_reminder_message()
    if content is None:
        print("ℹ️ 当前没有地区进入高峰前1小时窗口，不发送消息")
        return
    url = generate_signed_url(token, secret)
    send_dingtalk_message(url, content)

if __name__ == "__main__":
    main()
