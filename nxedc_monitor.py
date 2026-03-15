#!/usr/bin/env python3
import requests
import smtplib
import ssl
import os
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from html import unescape

REDDIT_RSS_URL = "https://www.reddit.com/r/fidgettoys/search.rss?q=nxedc"

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "zienow.559@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "rqssrywwmyghqqzx")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "559@cometspark.cc")

print(f"开始监测... {datetime.now()}")

HEADERS = {"User-Agent": "NXEDC-Monitor/1.0"}

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
    print("搜索Reddit RSS...")
    try:
        r = requests.get(REDDIT_RSS_URL, headers=HEADERS, timeout=30)
        print(f"状态码: {r.status_code}, 长度: {len(r.text)}")
        
        if r.status_code == 200:
            posts = []
            text = r.text
            
            # 使用正则表达式提取 entry
            entry_pattern = r'<entry>(.*?)</entry>'
            entries = re.findall(entry_pattern, text, re.DOTALL)
            print(f"找到 {len(entries)} 个条目")
            
            for entry in entries:
                # 提取 title
                title_match = re.search(r'<title>([^<]+)</title>', entry)
                title = unescape(title_match.group(1)) if title_match else ""
                
                # 提取 link
                link_match = re.search(r'<link href="([^"]+)"', entry)
                link = link_match.group(1) if link_match else ""
                
                # 提取 author
                author_match = re.search(r'<author><name>([^<]+)</name></author>', entry)
                author = author_match.group(1) if author_match else "unknown"
                
                # 提取 id
                id_match = re.search(r'<id>([^<]+)</id>', entry)
                post_id = id_match.group(1) if id_match else ""
                
                if title:
                    posts.append({
                        "title": title,
                        "link": link,
                        "author": author,
                        "id": post_id
                    })
            
            print(f"解析到 {len(posts)} 个帖子")
            return posts
    except Exception as e:
        print(f"搜索错误: {e}")
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
        report.append(f"链接: {p.get('link', '')}")
    
    send_email("\n".join(report))

if __name__ == "__main__":
    main()
