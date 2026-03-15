#!/usr/bin/env python3
import requests
import smtplib
import ssl
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

REDDIT_SEARCH_URL = "https://www.reddit.com/r/fidgettoys/search.json"
QUERY = "nxedc"

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "zienow.559@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "rqssrywwmyghqqzx")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "559@cometspark.cc")

print(f"开始监测... {datetime.now()}")

HEADERS = {
    "User-Agent": "NXEDC-Monitor/1.0",
    "Accept": "application/json"
}

def translate(text):
    if not text: return ""
    try:
        r = requests.get("https://translate.googleapis.com/translate_a/single",
            params={"client": "gtx", "sl": "auto", "tl": "zh-CN", "dt": "t", "q": text[:500]}, timeout=10)
        if r.status_code == 200:
            return "".join([i[0] for i in r.json()[0] if i[0]])
    except Exception as e:
        print(f"翻译错误: {e}")
    return text

def search_posts():
    print("搜索Reddit...")
    try:
        r = requests.get(REDDIT_SEARCH_URL, headers=HEADERS, params={"q": QUERY, "sort": "new", "limit": 25}, timeout=30)
        print(f"状态码: {r.status_code}")
        print(f"响应内容: {r.text[:200]}")
        if r.status_code == 200:
            data = r.json()
            children = data.get("data", {}).get("children", [])
            print(f"找到 {len(children)} 个帖子")
            return [c.get("data", {}) for c in children]
    except Exception as e:
        print(f"搜索错误: {e}")
    return []

def get_comments(post_id):
    try:
        r = requests.get(f"https://www.reddit.com/r/fidgettoys/comments/{post_id}.json", headers=HEADERS, timeout=30)
        if r.status_code == 200:
            return r.json()[1]["data"]["children"]
    except: pass
    return []

def send_email(body):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"NXEDC 舆情报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECIPIENT_EMAIL
        msg.attach(MIMEText(body.replace("\n", "<br>"), "html"))
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=ssl.create_default_context()) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
        print("邮件发送成功!")
    except Exception as e:
        print(f"邮件错误: {e}")

def main():
    posts = search_posts()
    if not posts:
        send_email(f"# NXEDC 舆情报告\n\n时间: {datetime.now()}\n\n未找到帖子")
        return
    
    report = [f"# NXEDC 舆情报告", f"时间: {datetime.now()}", "---"]
    for p in posts[:10]:
        title = p.get("title", "")
        title_zh = translate(title)
        report.append(f"\n## {title_zh}")
        report.append(f"原文: {title}")
        report.append(f"发帖人: {p.get('author')}")
        report.append(f"链接: https://reddit.com{p.get('permalink')}")
        
        comments = get_comments(p.get("id"))
        nxedc_cmts = [c["data"] for c in comments if "nxedc" in c["data"].get("body", "").lower()]
        if nxedc_cmts:
            report.append(f"\n### 相关评论:")
            for c in nxedc_cmts[:5]:
                report.append(f"- {c.get('author')}: {translate(c.get('body', ''))}")
    
    send_email("\n".join(report))

if __name__ == "__main__":
    main()
