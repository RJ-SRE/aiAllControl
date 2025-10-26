# 🧠 MacMind — AI 驱动的 macOS 智能助手
##deamo-link:** https://www.bilibili.com/video/BV16zszzxEuj/**
author:RJ
assistant：WQ、DH
date:2025-10-26-21：00
---
> 让你的 Mac 能听懂、会思考、可执行的 AI 控制系统

**MacMind** 通过集成七牛云大模型,让你用自然语言控制 macOS:
- 🔍 智能搜索和安装软件
- 🎮 控制应用程序
- 🔔 管理系统通知
- ⌨️ 配置快捷键

---

## 🚀 快速开始

### 环境要求
- macOS 10.15+
- Homebrew
- Python 3.8+
- 七牛云 API Key

### 安装

```bash
# 1. 克隆项目
git clone https://github.com/RJ-SRE/aiAllControl.git
cd aiAllControl

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置 API Key
mkdir -p ~/.macmind
cp config.example.json ~/.macmind/config.json
vim ~/.macmind/config.json  # 填入 API Key

# 4. 运行
python3 macmind.py --help
```

### 基本用法

```bash
# 搜索软件
python3 macmind.py search 绘图软件

# 安装软件
python3 macmind.py install drawio

# 列出已安装软件
python3 macmind.py list

# 控制应用
python3 macmind.py mac open Safari
python3 macmind.py mac quit "网易云音乐"

# 交互式对话
python3 macmind.py chat
```

---

## 🎨 前端交互完整教程

本章节详细介绍如何通过Web前端与MacMind进行交互,实现各种智能操作。

### 📱 第一步: 启动MacMind Web服务

#### 1.1 准备环境

确保已完成安装和配置(参见上方[快速开始](#-快速开始)章节):

```bash
# 验证Python环境
python3 --version  # 需要 3.8+

# 验证依赖安装
pip list | grep -E "flask|socketio"
```

#### 1.2 启动服务

**推荐方式 - 使用启动脚本:**

```bash
cd /path/to/aiAllControl
chmod +x start_web.sh    # 首次使用需要添加执行权限
./start_web.sh
```

**备用方式 - 直接启动:**

```bash
python3 server/app.py
```

#### 1.3 确认服务启动成功

看到以下输出表示成功:

```

### 1. 智能软件管理
```bash
> 帮我安装一个可以画流程图的工具
🤖 推荐 draw.io (Apache-2.0)
🪄 执行: brew install drawio
✅ 安装完成!
```

### 2. 应用控制
```bash
# 打开/关闭应用
python3 macmind.py mac open Safari
python3 macmind.py mac quit Discord

# 查询状态
python3 macmind.py mac status Safari
```

### 3. 通知管理
```bash
# 管理应用通知权限
python3 macmind.py notification disable Safari
python3 macmind.py notification info Discord
```

### 4. 快捷键配置
```bash
# 创建快捷键
python3 macmind.py shortcut create 'Command+L' '打开应用' Safari

# 检查冲突
python3 macmind.py shortcut check 'Command+L'
```

---

## 📝 配置说明

配置文件位置: `~/.macmind/config.json`

### 必需配置
```json
{
  "qiniu_api_key": "your-api-key",
  "qiniu_base_url": "https://openai.qiniu.com/v1",
  "qiniu_model": "gpt-4"
}
```

### 可选配置
```json
{
  "homebrew_path": "/opt/homebrew/bin/brew",
  "max_search_results": 5,
  "auto_install": false,
  "cache_ttl": 3600,
  "log_level": "INFO"
}
```

**配置优先级**: 环境变量 > 配置文件 > 默认值

---

## 🛠️ 技术架构

```yaml
后端: Python 3.8+
AI服务: 七牛云大模型 (OpenAI 兼容接口)
macOS自动化: osascript, Hammerspoon, subprocess
包管理: Homebrew
架构: DDD + Repository 模式
```

---

## 🔧 常见问题

**Q: Homebrew not found**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Q: API 请求失败**
```bash
# 检查配置
echo $QINIU_API_KEY
python3 -c "from infrastructure.config import config; print(config.get('qiniu_api_key'))"
```

**Q: 权限错误**
```bash
chmod 755 ~/.macmind
```

---

## 📊 功能特性对比

| 功能 | 可行性 | 复杂度 | 关键依赖 |
|------|--------|--------|----------|
| 软件安装 | ✅ 高 | 低 | Homebrew, LLM |
| 应用控制 | ✅ 高 | 中 | AppleScript |
| 快捷键配置 | ⚠️ 中 | 高 | 系统权限 |

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

提交前请确保:
- 代码符合项目规范
- 添加必要的测试
- 更新相关文档

---

## 📄 许可证

MIT License

---

## 🙏 致谢

- [Anthropic Claude](https://www.anthropic.com/claude)
- [Homebrew](https://brew.sh/)
- [Hammerspoon](https://www.hammerspoon.org/)
