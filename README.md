# 🧠 MacMind — AI 驱动的自学习电脑操作管家

> 一套让你的电脑"能听懂、会思考、可执行"的 AI 控制系统。  
> 不再是命令行助手，而是具备自主感知的数字管家。

---

## 🧩 项目简介

**MacMind** 是一个运行于 macOS 的 AI 系统控制框架。  
通过集成七牛云大模型推理服务，MacMind 能够：
- 理解自然语言指令
- 自动搜索和推荐软件
- 控制 macOS 应用程序
- 管理系统通知和快捷键

让 AI 不再依赖硬编码逻辑，而是通过自然语言指令，  
自动生成操作计划、执行系统命令，并持续学习用户偏好。

你只需告诉它：
> "帮我装个绘图软件"  
> "关闭 Discord 的通知"  
> "设置一个快捷键打开工作区应用"

它会：
- 理解意图；
- 自主检索合适方案；
- 通过 Bash / AppleScript 自动执行；
- 并在安全沙盒中反馈执行结果。

---

## 🧠 核心功能

### 🎯 1. 软件自动检索与下载

**可行性：✅ 高度可行 | 复杂度：低**

#### 功能特性
- 解析自然语言需求（例如"绘图软件"、"视频剪辑工具"）
- 自动搜索可用应用（如 Krita、Inkscape、Final Cut）
- 智能选择最佳下载途径（App Store / Homebrew / dmg）
- 验证软件许可证类型，优先推荐免费开源软件
- 匹配版本兼容性，检查 macOS 版本要求
- 执行安装命令并追踪进度

#### 使用示例
```bash
> 帮我安装一个可以画流程图的工具
🤖 检测到需求：绘图类 → 推荐 draw.io
🔍 检查许可证：Apache 2.0（免费）
🪄 执行：brew install drawio
✅ 安装完成！
```

#### 技术实现
```bash
# 查询软件
brew search <keyword>
brew info <formula>  # 获取版本、许可证

# 智能筛选
- 检查许可证类型（MIT, Apache, GPL 等免费协议）
- 匹配版本兼容性（macOS 版本）
- 优先推荐活跃维护的软件

# 自动安装
brew install <formula>
```

---

### 🎮 2. 自然语言控制 macOS 应用

**可行性：✅ 高度可行 | 复杂度：中**

#### 功能特性
- 通过自然语言关闭/打开应用程序
- 管理应用通知权限
- 控制应用行为和设置
- 实时权限状态检测

#### 使用示例
```bash
> 帮我关闭网易云音乐
🤖 正在关闭"网易云音乐"...
✅ 已关闭

> 帮我关闭网易云的消息通知权限
🤖 正在修改通知权限...
⚠️  需要"辅助功能"权限，请前往系统设置授权
✅ 权限已更新
```

#### 技术实现
```applescript
# 关闭应用
osascript -e 'quit app "网易云音乐"'

# 打开应用
open -a "网易云音乐"

# 查询通知权限
sqlite3 ~/Library/Application\ Support/NotificationCenter/db/db \
  "SELECT * FROM app_info WHERE bundleid='com.netease.163music'"

# 修改权限（需辅助功能权限）
tccutil reset Notifications com.netease.163music
```

#### 权限要求
⚠️ **需要系统权限**
- 首次运行需引导用户授予"辅助功能"权限
- 在"系统偏好设置 → 安全性与隐私 → 隐私 → 辅助功能"添加程序
- 维护常见应用的 Bundle ID 映射表

---

### ⌨️ 3. AI 辅助快捷键配置

**可行性：⚠️ 中等可行 | 复杂度：高**

#### 功能特性
- 通过自然语言设置全局快捷键
- 同时启动多个应用
- 自动检测快捷键冲突
- 支持复杂的组合操作

#### 使用示例
```bash
> 我想同时打开企业微信和 WPS，快捷键设置为 Command + L
🤖 检测快捷键冲突：Command+L 已被"锁定屏幕"占用
💡 建议使用：Command+Shift+L
✅ 快捷键已配置
```

#### 技术实现

**方案 A：系统服务（推荐）**
```bash
# 创建 Automator 服务
# ~/Library/Services/OpenApps.workflow
```
- 在"系统偏好设置 → 键盘 → 快捷键 → 服务"设置
- 需要编程方式修改 plist 文件

**方案 B：Hammerspoon（更灵活）**
```lua
# 安装 Hammerspoon
brew install hammerspoon

# 配置快捷键
hs.hotkey.bind({"cmd"}, "L", function()
  hs.application.launchOrFocus("企业微信")
  hs.application.launchOrFocus("WPS")
end)
```

#### 应用启动脚本
```applescript
# 同时打开多个应用
tell application "企业微信" to activate
tell application "WPS" to activate
```

#### 限制说明
⚠️ **技术限制**
- 系统快捷键可能存在冲突
- 需要"辅助功能"和"输入监控"权限
- 首次配置需手动授权，非完全自动化
- 系统完整性保护（SIP）限制直接修改系统配置

---

## 📊 可行性总结

| 场景 | 可行性 | 复杂度 | 关键依赖 |
|------|--------|--------|----------|
| 1. AI 辅助软件安装 | ✅ 高 | 低 | Homebrew API, LLM |
| 2. 自然语言控制应用 | ✅ 高 | 中 | AppleScript/osascript |
| 3. AI 辅助快捷键配置 | ⚠️ 中 | 高 | 系统权限, plist 操作 |

---

## 🛠️ 技术架构

### 技术栈
```yaml
后端框架: Python 3.8+
LLM 集成: 七牛云大模型推理服务 (OpenAI 兼容接口)
macOS 自动化: 
  - osascript (AppleScript)
  - Hammerspoon (快捷键管理)
  - subprocess (执行 shell 命令)
包管理: Homebrew
前端界面: CLI (命令行)
架构设计: DDD (领域驱动设计) + Repository 模式
```

### 开发阶段
```
阶段 1: 实现场景 1（软件安装助手）
  ├─ LLM 集成与提示词工程
  ├─ Homebrew API 封装
  └─ 许可证识别逻辑

阶段 2: 实现场景 2（应用控制）
  ├─ AppleScript 命令库
  ├─ 权限申请引导界面
  └─ 应用 Bundle ID 数据库

阶段 3: 实现场景 3（快捷键配置）
  ├─ Hammerspoon 集成
  ├─ 冲突检测机制
  └─ 配置持久化
```

---

## 🚀 快速开始

### 环境要求
- **操作系统**: macOS 10.15+ (Catalina 或更高版本)
- **包管理器**: Homebrew (用于安装和管理软件包)
- **Python**: Python 3.8+ (建议 3.11+)
- **API 密钥**: 七牛云 API Key (用于 AI 功能)

### 安装步骤

#### 1. 克隆项目
```bash
git clone https://github.com/RJ-SRE/aiAllControl.git
cd aiAllControl
```

#### 2. 安装依赖

**方式 A: 标准安装**
```bash
pip install -r requirements.txt
```

**方式 B: 开发模式安装(推荐,包含测试工具)**
```bash
pip install -e ".[dev]"
```

#### 3. 配置 API Key

MacMind 支持两种配置方式,优先级:环境变量 > 配置文件

**方式 1: 使用配置文件(推荐)**
```bash
# 创建配置目录
mkdir -p ~/.macmind

# 复制示例配置文件
cp config.example.json ~/.macmind/config.json

# 编辑配置文件,填入你的七牛云 API Key
vim ~/.macmind/config.json  # 或使用其他编辑器
```

配置文件说明请参阅下方的 [📝 配置文件说明](#-配置文件说明) 章节。

**方式 2: 使用环境变量**
```bash
# 设置七牛云 API 密钥
export QINIU_API_KEY="your-qiniu-api-key-here"

# 可选:永久配置(添加到 ~/.zshrc 或 ~/.bash_profile)
echo 'export QINIU_API_KEY="your-qiniu-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

#### 4. 验证安装
```bash
# 检查 Python 版本
python3 --version

# 检查 Homebrew 是否安装
brew --version

# 验证配置是否正确
python3 -c "from infrastructure.config import config; print('配置加载成功' if config.get('qiniu_api_key') else '请设置 API Key')"
```

### 运行程序

#### 基本用法
```bash
# 运行主程序(交互式命令行界面)
python3 macmind.py
```

#### 命令行参数

MacMind 提供多个子命令来执行不同操作:

**1. 搜索软件包**
```bash
# 搜索绘图软件
python3 macmind.py search 绘图软件

# 搜索视频编辑工具
python3 macmind.py search "video editor"
```

**2. 安装软件包**
```bash
# 安装指定软件包
python3 macmind.py install drawio

# 安装多个软件包
python3 macmind.py install vim git wget
```

**3. 列出已安装软件**
```bash
# 列出所有通过 Homebrew 安装的软件
python3 macmind.py list
```

**4. 获取软件信息**
```bash
# 查看软件详细信息
python3 macmind.py info vim
```

**5. 帮助信息**
```bash
# 查看所有可用命令
python3 macmind.py --help

# 查看特定命令的帮助
python3 macmind.py search --help
```

### 使用示例

#### 示例 1: 智能搜索并安装绘图软件
```bash
$ python3 macmind.py search 绘图软件
🤖 正在分析需求...
🔍 搜索到以下软件:
1. drawio - 流程图和图表绘制工具 (Apache-2.0)
2. inkscape - 矢量图形编辑器 (GPL-3.0)
3. krita - 数字绘画软件 (GPL-3.0)

$ python3 macmind.py install drawio
🤖 准备安装 drawio...
✅ 安装成功!
```

#### 示例 2: 列出已安装的开发工具
```bash
$ python3 macmind.py list
📦 已安装的软件包:
- vim (9.0.1234)
- git (2.40.0)
- python@3.11 (3.11.5)
...
```

### 常见问题

#### Q1: 提示 "Homebrew not found"
**解决方案**:
```bash
# 安装 Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 如果 Homebrew 安装在非默认位置,修改配置文件
vim ~/.macmind/config.json
# 更新 homebrew_path 字段为实际路径
```

#### Q2: API 请求失败
**解决方案**:
```bash
# 检查 API Key 是否正确配置
echo $QINIU_API_KEY

# 检查网络连接
curl -I https://openai.qiniu.com

# 验证 API Key 是否有效(联系七牛云获取)
```

#### Q3: 权限错误
**解决方案**:
```bash
# 确保配置目录有写权限
chmod 755 ~/.macmind

# 某些操作可能需要 sudo (不推荐,优先使用 Homebrew)
# Homebrew 安装通常不需要 sudo
```

#### Q4: Python 版本不兼容
**解决方案**:
```bash
# 使用 pyenv 管理 Python 版本
brew install pyenv
pyenv install 3.11.5
pyenv global 3.11.5

# 重新安装依赖
pip install -r requirements.txt
```

### 高级配置

#### 自定义配置路径
```bash
# 使用自定义配置文件
export MACMIND_CONFIG="/path/to/custom/config.json"
python3 macmind.py
```

#### 日志配置
```bash
# 日志文件位置: ~/.macmind/logs/macmind.log
# 查看日志
tail -f ~/.macmind/logs/macmind.log

# 清理旧日志
rm ~/.macmind/logs/*.log
```

#### 启用调试模式
```python
# 在 ~/.macmind/config.json 中添加
{
  "log_level": "DEBUG",
  "verbose": true
}
```

---

## 📝 配置文件说明

MacMind 使用 JSON 格式的配置文件,位于 `~/.macmind/config.json`。下面详细说明每个配置项的作用。

### 配置文件位置
- **默认路径**: `~/.macmind/config.json`
- **示例文件**: 项目根目录的 `config.example.json`
- **自动创建**: 如果目录不存在,程序会自动创建 `~/.macmind` 目录

### 完整配置示例

```json
{
  "qiniu_api_key": "your-qiniu-api-key-here",
  "qiniu_base_url": "https://openai.qiniu.com/v1",
  "qiniu_model": "gpt-4",
  "homebrew_path": "/opt/homebrew/bin/brew",
  "max_search_results": 5,
  "auto_install": false,
  "preferred_license": ["MIT", "Apache-2.0", "GPL-3.0"],
  "cache_ttl": 3600,
  "log_level": "INFO",
  "verbose": false
}
```

### 配置项详细说明

#### 🔑 AI 服务配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `qiniu_api_key` | string | `null` | **七牛云 API 密钥**<br>• 必填项,用于调用 AI 服务<br>• 建议通过环境变量 `QINIU_API_KEY` 设置<br>• 不会保存到配置文件(安全考虑) |
| `qiniu_base_url` | string | `"https://openai.qiniu.com/v1"` | **七牛云 API 端点**<br>• AI 服务的 API 地址<br>• 默认使用七牛云 OpenAI 兼容接口<br>• 一般无需修改 |
| `qiniu_model` | string | `"gpt-4"` | **使用的 AI 模型**<br>• 指定使用的大语言模型<br>• 支持: `gpt-4`, `gpt-3.5-turbo` 等<br>• 不同模型性能和成本不同 |

**示例: 配置 AI 服务**
```json
{
  "qiniu_base_url": "https://openai.qiniu.com/v1",
  "qiniu_model": "gpt-4"
}
```

> ⚠️ **安全提示**: API 密钥建议使用环境变量设置,不要直接写入配置文件

#### 🍺 Homebrew 配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `homebrew_path` | string | `"/opt/homebrew/bin/brew"` | **Homebrew 可执行文件路径**<br>• Apple Silicon (M1/M2) Mac: `/opt/homebrew/bin/brew`<br>• Intel Mac: `/usr/local/bin/brew`<br>• 自定义安装路径需修改此配置 |

**示例: Intel Mac 配置**
```json
{
  "homebrew_path": "/usr/local/bin/brew"
}
```

**如何查找 Homebrew 路径**:
```bash
which brew
# 输出: /opt/homebrew/bin/brew 或 /usr/local/bin/brew
```

#### 🔍 搜索和安装配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `max_search_results` | integer | `5` | **最大搜索结果数**<br>• 限制搜索返回的软件包数量<br>• 范围: 1-20<br>• 过多会影响阅读体验 |
| `auto_install` | boolean | `false` | **自动安装模式**<br>• `true`: 安装时不需要确认<br>• `false`: 每次安装需要用户确认<br>• **建议保持 `false`(安全)** |
| `preferred_license` | array | `["MIT", "Apache-2.0", "GPL-3.0"]` | **优先许可证列表**<br>• AI 搜索时优先推荐这些开源协议<br>• 确保推荐的软件免费可用<br>• 支持: MIT, Apache-2.0, GPL-3.0, BSD 等 |

**示例: 搜索配置优化**
```json
{
  "max_search_results": 10,
  "auto_install": false,
  "preferred_license": ["MIT", "Apache-2.0", "GPL-3.0", "BSD-3-Clause"]
}
```

#### ⚡ 性能配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `cache_ttl` | integer | `3600` | **缓存有效期(秒)**<br>• 搜索结果缓存时间<br>• `3600` = 1小时<br>• 设为 `0` 禁用缓存 |

**示例: 缓存配置**
```json
{
  "cache_ttl": 7200
}
```

#### 📊 日志配置 (可选)

这些配置项是可选的,默认情况下不需要配置。

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `log_level` | string | `"INFO"` | **日志级别**<br>• `DEBUG`: 详细调试信息<br>• `INFO`: 一般信息(推荐)<br>• `WARNING`: 警告信息<br>• `ERROR`: 仅错误信息 |
| `verbose` | boolean | `false` | **详细输出模式**<br>• `true`: 输出详细执行信息<br>• `false`: 简洁输出 |

**示例: 开启调试模式**
```json
{
  "log_level": "DEBUG",
  "verbose": true
}
```

### 配置优先级

MacMind 按以下优先级加载配置(从高到低):

1. **环境变量** (最高优先级)
   - `QINIU_API_KEY`: 七牛云 API 密钥
   - `MACMIND_CONFIG`: 自定义配置文件路径

2. **配置文件**
   - `~/.macmind/config.json`

3. **默认值** (最低优先级)
   - 代码中定义的默认配置

### 配置文件管理

#### 创建配置文件
```bash
# 从示例创建
mkdir -p ~/.macmind
cp config.example.json ~/.macmind/config.json

# 编辑配置
vim ~/.macmind/config.json
```

#### 验证配置
```bash
# 验证配置是否有效
python3 -c "from infrastructure.config import config; print('✅ 配置有效' if config.validate() else '❌ 配置无效')"
```

#### 查看当前配置
```bash
# 查看配置文件
cat ~/.macmind/config.json

# 或使用 Python
python3 -c "from infrastructure.config import config; import json; print(json.dumps(config._config, indent=2, ensure_ascii=False))"
```

#### 重置配置
```bash
# 删除配置文件,将使用默认配置
rm ~/.macmind/config.json

# 或重新复制示例文件
cp config.example.json ~/.macmind/config.json
```

### 最佳实践

#### ✅ 推荐做法
1. **API 密钥使用环境变量**: 不要将密钥写入配置文件
   ```bash
   export QINIU_API_KEY="your-key"
   ```

2. **保持 `auto_install` 为 `false`**: 确保安装前有确认步骤

3. **根据需求调整 `max_search_results`**: 新手使用 5,熟练后可增加到 10

4. **定期备份配置文件**:
   ```bash
   cp ~/.macmind/config.json ~/.macmind/config.json.backup
   ```

#### ❌ 避免做法
1. **不要将配置文件提交到 Git**: 可能包含敏感信息
2. **不要设置过长的 `cache_ttl`**: 可能导致数据过时
3. **不要在生产环境开启 DEBUG**: 会产生大量日志

### 配置问题排查

#### 问题: 提示 "API Key not found"
```bash
# 检查环境变量
echo $QINIU_API_KEY

# 检查配置文件
cat ~/.macmind/config.json | grep qiniu_api_key

# 验证配置
python3 -c "from infrastructure.config import config; print(config.get('qiniu_api_key'))"
```

#### 问题: Homebrew 路径错误
```bash
# 查找正确路径
which brew

# 更新配置文件
vim ~/.macmind/config.json
# 修改 "homebrew_path" 为正确路径
```

#### 问题: 配置文件损坏
```bash
# 验证 JSON 格式
python3 -m json.tool ~/.macmind/config.json

# 如果格式错误,重新创建
cp config.example.json ~/.macmind/config.json
```

---

## 🔒 安全建议

- ✅ 软件安装前展示详细信息供用户确认
- ✅ 权限修改记录日志，支持回滚
- ✅ 限制可控制的应用范围（白名单机制）
- ✅ 避免执行用户提供的原始 shell 命令
- ✅ 敏感操作（安装软件、修改权限）需二次确认

---

## 💡 用户体验优化

1. **首次启动向导**：引导用户授予必要权限
2. **权限检查**：实时检测权限状态，提示用户补充
3. **安全确认**：敏感操作需明确确认
4. **错误恢复**：操作失败时提供明确解决方案
5. **操作日志**：记录所有自动化操作，支持审计和回滚

---

## 📝 开发路线图

- [x] 需求分析和可行性研究
- [ ] 实现 AI 辅助软件安装功能
- [ ] 实现自然语言应用控制
- [ ] 实现快捷键配置功能
- [ ] 开发权限管理系统
- [ ] 构建用户界面（CLI/GUI）
- [ ] 安全审计和测试
- [ ] 文档完善和示例补充

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

在提交 PR 前，请确保：
1. 代码符合项目规范
2. 添加必要的测试
3. 更新相关文档
4. 遵循安全最佳实践

---

## 📄 许可证

MIT License

---

## 🙏 致谢

本项目基于以下技术和工具构建：
- [Anthropic Claude](https://www.anthropic.com/claude)
- [Homebrew](https://brew.sh/)
- [Hammerspoon](https://www.hammerspoon.org/)
- [AppleScript](https://developer.apple.com/library/archive/documentation/AppleScript/Conceptual/AppleScriptLangGuide/)

---

**结论**：三个场景均技术可行，场景 1 和 2 实现难度较低，场景 3 因 macOS 安全机制限制，需依赖第三方工具并要求用户手动授权。建议优先开发场景 1 和 2，积累用户反馈后再完善场景 3。
