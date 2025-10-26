#!/bin/bash
# MacMind Web服务启动脚本

echo "================================"
echo "  MacMind Web 服务启动"
echo "================================"
echo ""

# 检查Python版本
PYTHON_VERSION=$(python3 --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+')
echo "✓ Python 版本: $PYTHON_VERSION"

# 检查依赖
echo ""
echo "检查依赖..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚠ Flask未安装,正在安装依赖..."
    pip3 install -r requirements.txt
else
    echo "✓ 依赖已安装"
fi

echo ""
echo "================================"
echo "  启动Web服务..."
echo "================================"
echo ""
echo "访问地址: http://localhost:5000"
echo "按 Ctrl+C 停止服务"
echo ""

# 启动服务
python3 server/app.py
