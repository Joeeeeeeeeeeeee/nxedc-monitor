# NXEDC 舆情监测

Reddit r/fidgettoys 板块 NXEDC 关键词舆情监测，每2小时自动执行。

## 功能
- 搜索包含 NXEDC 的帖子
- 翻译标题和内容为中文
- 提取直接提到 NXEDC 的评论
- 提取其他相关评论
- 发送邮件报告

## GitHub Actions 设置

### 1. 创建仓库
1. 登录 GitHub: https://github.com
2. 创建新仓库: `nxedc-monitor`
3. **不要**勾选 "Add a README file"

### 2. 推送代码
在终端执行：
```bash
cd /Users/joe/CodeBuddy
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/Joeeeeeeeeeeeee/nxedc-monitor.git
git push -u origin main
```

### 3. 设置 Secrets
仓库创建后，在 GitHub 上设置：
1. 进入仓库 → Settings → Secrets and variables → Actions
2. 添加以下 Secrets:

| Name | Value |
|------|-------|
| SMTP_SERVER | smtp.gmail.com |
| SMTP_PORT | 465 |
| SENDER_EMAIL | zienow.559@gmail.com |
| SENDER_PASSWORD | rqssrywwmyghqqzx |
| RECIPIENT_EMAIL | 559@cometspark.cc |

### 4. 验证
- 手动触发: 进入 Actions → NXEDC 舆情监测 → Run workflow
- 自动运行: 每2小时执行一次

## 本地运行
```bash
python3 nxedc_monitor.py
```
