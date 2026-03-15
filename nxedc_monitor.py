#!/usr/bin/env python3
"""
Reddit NXEDC 舆情监测工具
"""

import requests
import smtplib
import ssl
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

REDDIT_SEARCH_URL = "https://www.reddit.com/r/fidgettoys/search/.json"
QUERY = "nxedc"
OUTPUT_FILE = "nxedc_sentiment_report.md"

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "zienow.559@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "rqssrywwmyghqqzx")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "559@cometspark.cc")

print(f"=== NXEDC Monitor Started ===")
print(f"SENDER_EMAIL: {SENDER_EMAIL}")
print(f"RECIPIENT_EMAIL: {RECIPIENT_EMAIL}")

HEADERS = {"User-Agent": "NXEDC-Monitor/1.0"}

def translate_to_chinese(text):
    if not text: return ""
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {"client": "gtx", "sl": "auto", "tl": "zh-CN", "dt": "t", "q": text[:500]}
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            return "".join([i[0] for i in r.json()[0] if i[0]])
    except Exception as e:
        print(f"翻译错误: {e}")
    return text

def search_posts():
    try:
        print("搜索Reddit帖子...")
        r = requests.get(REDDIT_SEARCH_URL, headers=HEADERS, params={"q": QUERY, "sort": "new", "limit": 25}, timeout=30)
        print(f"Reddit状态码: {r.status_code}")
        if r.status_code == 200:
            return [c["data"] for c in r.json()["data"]["children"]]
    except Exception as e:
        print(f"搜索错误: {e}")
    return []

def get_comments(post_id):
    try:
        r = requests.get(f"https://www.reddit.com/r/fidgettoys/comments/{post_id}/.json", headers=HEADERS, timeout=30)
        if r.status_code == 200:
            return r.json()[1]["data"]["children"]
    except: pass
    return []

def format_time(ts):
    if not ts: return "未知"
    try: return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except: return "未知"

def send_email(body):
    print("发送邮件...")
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"NXEDC 舆情报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECIPIENT_EMAIL
        msg.attach(MIMEText(body.replace("\n", "<br>"), "html"))
        msg.attach(MIMEText(body, "plain"))
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=ctx) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
        print("邮件发送成功!")
    except Exception as e:
        print(f"邮件错误: {e}")
        import traceback
        traceback.print_exc()

def main():
    posts = search_posts()
    if not posts:
        send_email(f"# NXEDC 舆情报告\n\n未找到帖子")
        return
    
    report = [f"# NXEDC 舆情报告", f"时间: {datetime.now()}", "---"]
    for p in posts[:10]:
        title_zh = translate_to_chinese(p.get("title", ""))
        report.append(f"\n## {title_zh}")
        report.append(f"发帖人: {p.get('author')}")
        report.append(f"时间: {format_time(p.get('created_utc'))}")
        report.append(f"链接: https://reddit.com{p.get('permalink')}")
        
        comments = get_comments(p.get("id"))
        nxedc_cmts = [c["data"] for c in comments if "nxedc" in c["data"].get("body", "").lower()]
        if nxedc_cmts:
            report.append(f"\n### NXEDC相关评论:")
            for c in nxedc_cmts[:5]:
                report.append(f"- {c.get('author')}: {translate_to_chinese(c.get('body', ''))}")
    
    result = "\n".join(report)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(result)
    send_email(result)

if __name__ == "__main__":
    main()
