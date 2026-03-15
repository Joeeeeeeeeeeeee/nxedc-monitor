#!/usr/bin/env python3
"""
Reddit NXEDC 舆情监测工具
每2小时自动执行，监测 Reddit 上关于 NXEDC 的帖子和评论
"""

import requests
import json
import time
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

# ============ 配置区域 ============
REDDIT_SEARCH_URL = "https://www.reddit.com/r/fidgettoys/search/.json"
QUERY = "nxedc"
OUTPUT_FILE = "nxedc_sentiment_report.md"
TRANSLATION_API = "google"  # google / deepl / custom

# 邮件配置 (支持环境变量)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "seizenow.559@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "rqssrywwmyghqqzx")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "559@cometspark.cc")

# Reddit API Headers (需要设置 User-Agent)
HEADERS = {
    "User-Agent": "NXEDC-Monitor/1.0"
}

# ============ 功能函数 ============

def translate_to_chinese(text, api="google"):
    """翻译文本到中文"""
    if not text:
        return ""
    
    if api == "google":
        # 使用 Google Translate API (免费)
        try:
            url = f"https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": "auto",
                "tl": "zh-CN",
                "dt": "t",
                "q": text
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                result = response.json()
                return "".join([item[0] for item in result[0] if item[0]])
        except Exception as e:
            print(f"翻译错误: {e}")
            return text
    
    return text


def search_reddit_posts(query, limit=25):
    """搜索 Reddit 帖子"""
    params = {
        "q": query,
        "sort": "new",
        "limit": limit,
        "t": "all"
    }
    
    try:
        response = requests.get(REDDIT_SEARCH_URL, headers=HEADERS, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"搜索错误: {e}")
    
    return None


def get_post_comments(post_id):
    """获取帖子评论"""
    url = f"https://www.reddit.com/r/fidgettoys/comments/{post_id}/.json"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"获取评论错误: {e}")
    
    return None


def parse_posts(data):
    """解析帖子数据"""
    posts = []
    
    try:
        children = data.get("data", {}).get("children", [])
        for child in children:
            post = child.get("data", {})
            posts.append({
                "id": post.get("id"),
                "title": post.get("title"),
                "content": post.get("selftext"),
                "author": post.get("author"),
                "created_utc": post.get("created_utc"),
                "permalink": post.get("permalink"),
                "url": f"https://reddit.com{post.get('permalink')}",
                "score": post.get("score"),
                "num_comments": post.get("num_comments")
            })
    except Exception as e:
        print(f"解析帖子错误: {e}")
    
    return posts


def parse_comments(comments_data, nxedc_keyword="nxedc"):
    """解析评论数据"""
    comments = []
    
    try:
        # 评论在 data[1]["data"]["children"]
        comment_list = comments_data[1]["data"]["children"]
        
        for comment in comment_list:
            comment_data = comment.get("data", {})
            body = comment_data.get("body", "")
            
            # 检查是否包含 NXEDC 关键词（不区分大小写）
            contains_nxedc = nxedc_keyword.lower() in body.lower()
            
            comments.append({
                "id": comment_data.get("id"),
                "author": comment_data.get("author"),
                "body": body,
                "created_utc": comment_data.get("created_utc"),
                "score": comment_data.get("score"),
                "contains_nxedc": contains_nxedc,
                "permalink": f"https://reddit.com{comment_data.get('permalink')}"
            })
    except Exception as e:
        print(f"解析评论错误: {e}")
    
    return comments


def format_timestamp(utc_timestamp):
    """格式化时间戳"""
    if not utc_timestamp:
        return "未知"
    
    try:
        dt = datetime.fromtimestamp(utc_timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return "未知"


def generate_report(posts_data):
    """生成舆情报告"""
    report_lines = []
    report_lines.append(f"# NXEDC 舆情监测报告")
    report_lines.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"监测来源: r/fidgettoys")
    report_lines.append("\n---\n")
    
    for post in posts_data:
        # 翻译标题和内容
        title_zh = translate_to_chinese(post["title"])
        content_zh = translate_to_chinese(post["content"]) if post["content"] else "（无正文）"
        
        report_lines.append(f"## 📌 {title_zh}")
        report_lines.append(f"\n**原文标题**: {post['title']}")
        report_lines.append(f"**发帖人**: {post['author']}")
        report_lines.append(f"**发帖时间**: {format_timestamp(post['created_utc'])}")
        report_lines.append(f"**帖子链接**: {post['url']}")
        report_lines.append(f"**点赞数**: {post['score']}")
        report_lines.append(f"**评论数**: {post['num_comments']}")
        report_lines.append(f"\n### 正文内容")
        report_lines.append(f"**中文翻译**: {content_zh}")
        report_lines.append(f"**原文**: {post['content'][:500]}..." if len(post.get('content', '')) > 500 else f"**原文**: {post.get('content', '无')}")
        report_lines.append("\n")
        
        # 获取评论
        comments_data = get_post_comments(post["id"])
        if comments_data:
            comments = parse_comments(comments_data)
            
            # 直接提到 NXEDC 的评论
            nxedc_comments = [c for c in comments if c["contains_nxedc"]]
            # 有关联但没直接提到 NXEDC 的评论（这里可以根据需要调整逻辑）
            related_comments = [c for c in comments if not c["contains_nxedc"]]
            
            if nxedc_comments:
                report_lines.append(f"### 💬 直接提到 NXEDC 的评论 ({len(nxedc_comments)}条)")
                for i, comment in enumerate(nxedc_comments[:10], 1):  # 限制显示数量
                    body_zh = translate_to_chinese(comment["body"])
                    report_lines.append(f"\n**{i}. {comment['author']}** ({format_timestamp(comment['created_utc'])})")
                    report_lines.append(f"中文翻译: {body_zh}")
                    report_lines.append(f"原文: {comment['body'][:200]}...")
                    report_lines.append(f"链接: {comment['permalink']}")
            
            if related_comments:
                report_lines.append(f"\n### 💬 其他热门评论 ({len(related_comments)}条)")
                for i, comment in enumerate(related_comments[:10], 1):  # 限制显示数量
                    body_zh = translate_to_chinese(comment["body"])
                    report_lines.append(f"\n**{i}. {comment['author']}** ({format_timestamp(comment['created_utc'])})")
                    report_lines.append(f"中文翻译: {body_zh}")
                    report_lines.append(f"原文: {comment['body'][:200]}...")
                    report_lines.append(f"链接: {comment['permalink']}")
        
        report_lines.append("\n---\n")
    
    return "\n".join(report_lines)


def send_email(subject, body, sender_email, recipient_email, password):
    """发送邮件"""
    try:
        # 创建邮件
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = recipient_email
        
        # 添加 HTML 和纯文本内容
        html_content = body.replace("\n", "<br>")
        html_part = MIMEText(html_content, "html", "utf-8")
        text_part = MIMEText(body, "plain", "utf-8")
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # 创建安全连接
        context = ssl.create_default_context()
        
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        
        print(f"邮件已发送到: {recipient_email}")
        return True
    except Exception as e:
        print(f"发送邮件错误: {e}")
        return False


def main():
    """主函数"""
    print(f"[{datetime.now()}] 开始监测 NXEDC 舆情...")
    
    # 搜索帖子
    print("正在搜索帖子...")
    data = search_reddit_posts(QUERY)
    
    if data:
        posts = parse_posts(data)
        print(f"找到 {len(posts)} 个帖子")
        
        # 生成报告
        report = generate_report(posts)
        
        # 保存报告
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"报告已保存到: {OUTPUT_FILE}")
        
        # 发送邮件
        if SENDER_EMAIL != "your_email@gmail.com" and SENDER_PASSWORD != "your_app_password":
            subject = f"NXEDC 舆情监测报告 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            send_email(subject, report, SENDER_EMAIL, RECIPIENT_EMAIL, SENDER_PASSWORD)
        else:
            print("请配置邮件 SMTP 设置")
    else:
        print("未获取到数据")


if __name__ == "__main__":
    main()
