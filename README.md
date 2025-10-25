# 🧠 MacMind — AI 驱动的自学习电脑操作管家

> 一套让你的电脑"能听懂、会思考、可执行"的 AI 控制系统。  
> 不再是命令行助手，而是具备自主感知的数字管家。

---

## 🧩 项目简介

**MacMind** 是一个运行于 macOS 的 AI 系统控制框架。  
它基于 **MCP（Model-Controlled Process）** 理念，  
让 AI 不再依赖硬编码逻辑，而是通过自然语言指令，  
自动生成操作计划、执行系统命令、管理权限，并持续学习用户偏好。

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
后端框架: Python/Node.js
LLM 集成: Anthropic Claude API / OpenAI GPT API
macOS 自动化: 
  - osascript (AppleScript)
  - Hammerspoon (快捷键管理)
  - subprocess (执行 shell 命令)
包管理: Homebrew
前端界面: 
  - CLI (命令行)
  - 或菜单栏应用 (Swift/Electron)
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
- macOS 10.15+
- Homebrew
- Python 3.8+ / Node.js 16+
- Claude API 或 OpenAI API Key

### 安装步骤
```bash
# 克隆项目
git clone https://github.com/RJ-SRE/aiAllControl.git
cd aiAllControl

# 安装依赖
pip install -r requirements.txt
# 或
npm install

# 配置 API Key (两种方式任选其一)

# 方式1: 使用配置文件 (推荐)
# 创建配置文件: ~/.macmind/config.json
mkdir -p ~/.macmind
cp config.example.json ~/.macmind/config.json
# 编辑 ~/.macmind/config.json，填入你的 API Key

# 方式2: 使用环境变量
export ANTHROPIC_API_KEY="your-api-key"

# 运行
python3 main.py
# 或
npm start
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
