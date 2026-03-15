#!/bin/bash
# NXEDC 舆情监测 - 一键设置脚本

echo "=== NXEDC 舆情监测设置 ==="
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3"
    exit 1
fi

# 添加定时任务
echo "正在设置定时任务 (每2小时执行)..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CRON_CMD="0 */2 * * * /usr/bin/python3 $SCRIPT_DIR/nxedc_monitor.py >> $SCRIPT_DIR/nxedc_monitor.log 2>&1"

# 检查是否已存在
EXISTING=$(crontab -l 2>/dev/null | grep "nxedc_monitor.py")
if [ -n "$EXISTING" ]; then
    echo "定时任务已存在，先移除旧的..."
    crontab -l 2>/dev/null | grep -v "nxedc_monitor.py" | crontab -
fi

# 添加新任务
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo "✓ 定时任务已设置"
echo ""
echo "当前定时任务:"
crontab -l | grep nxedc
echo ""
echo "=== 设置完成 ==="
echo "请确保已在 nxedc_monitor.py 中配置邮件 SMTP 设置"
