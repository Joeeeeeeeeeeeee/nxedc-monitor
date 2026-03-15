#!/bin/bash
# 绕过 xcrun 错误，直接调用 Python

export PATH="/usr/bin:/bin:/usr/local/bin:$PATH"
unset DEVELOPER_DIR

cd /Users/joe/CodeBuddy
/usr/bin/python3 nxedc_monitor.py
