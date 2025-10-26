# MacMind Web界面使用指南

MacMind 阶段2 - 赛博朋克风格Web界面

## 🎯 功能特性

### 核心功能
- ✅ **实时AI对话** - 通过WebSocket实现实时通信
- ✅ **工具执行可视化** - 实时显示AI工具调用状态
- ✅ **赛博朋克UI** - 霓虹色彩、扫描线、Glitch特效
- ✅ **响应式设计** - 支持桌面和移动设备

### 技术栈
- **后端**: Flask + Flask-SocketIO
- **前端**: HTML5 + CSS3 + Vanilla JavaScript
- **通信**: WebSocket (Socket.IO)
- **风格**: Cyberpunk 2077风格设计

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖:
- flask>=3.0.0
- flask-cors>=4.0.0
- flask-socketio>=5.3.0
- python-socketio>=5.10.0
- eventlet>=0.33.0

### 2. 启动Web服务

**方式1: 使用启动脚本 (推荐)**
```bash
./start_web.sh
```

**方式2: 直接启动**
```bash
python3 server/app.py
```

### 3. 访问界面

打开浏览器访问:
```
http://localhost:5000
```

## 📖 使用说明

### 界面布局

```
┌─────────────────────────────────────────────┐
│  [MacMind]  ● CONNECTED      ⟲    ⓘ       │  状态栏
├─────────────────────────────────────────────┤
│                                             │
│  对话窗口                                    │
│  - 欢迎消息                                  │
│  - 用户消息 (蓝色)                           │
│  - AI回复 (绿色)                             │
│  - 工具执行 (紫色)                           │
│                                             │
├─────────────────────────────────────────────┤
│  >> 输入指令...                    [发送]    │  输入区
└─────────────────────────────────────────────┘
```

### 功能按钮

- **⟲ 清空对话** - 清除所有对话历史
- **ⓘ 系统信息** - 查看系统状态 (待实现)

### 使用示例

#### 示例1: 搜索软件
```
用户: 帮我搜索一个绘图软件
AI: 🔧 [执行工具: search_software] ✅
    我找到了以下绘图软件:
    1. drawio - 流程图工具
    2. inkscape - 矢量图编辑器
    3. krita - 数字绘画软件
```

#### 示例2: 安装软件
```
用户: 安装 drawio
AI: 🔧 [执行工具: install_software] ✅
    已成功安装 drawio!
```

#### 示例3: 控制应用
```
用户: 打开 Safari
AI: 🔧 [执行工具: open_app] ✅
    已为您打开 Safari!
```

## 🎨 界面特效

### 赛博朋克元素

1. **霓虹色彩**
   - 粉色 (#ff006e) - Logo和强调
   - 蓝色 (#00f5ff) - 用户消息和边框
   - 绿色 (#00ff9f) - AI消息和成功状态
   - 紫色 (#8b00ff) - 工具执行提示

2. **动画效果**
   - 扫描线动画 (scanline)
   - Glitch故障艺术效果
   - 霓虹发光效果 (glow-pulse)
   - 状态指示灯闪烁 (pulse)

3. **背景特效**
   - 网格背景
   - 渐变背景色
   - 半透明毛玻璃效果

## 🔧 API接口

### REST API

#### 1. 健康检查
```http
GET /api/health
```
响应:
```json
{
    "status": "ok",
    "service": "MacMind Web API",
    "version": "1.0.0"
}
```

#### 2. 同步聊天
```http
POST /api/chat
Content-Type: application/json

{
    "message": "帮我搜索绘图软件"
}
```
响应:
```json
{
    "success": true,
    "message": "AI回复内容",
    "tool_calls": [
        {
            "function": "search_software",
            "arguments": {"query": "绘图软件"},
            "result": {"success": true, "data": {...}}
        }
    ]
}
```

#### 3. 获取历史
```http
GET /api/history
```

#### 4. 清空历史
```http
POST /api/clear
```

### WebSocket 事件

#### 客户端 → 服务器

| 事件 | 数据 | 说明 |
|------|------|------|
| `chat_message` | `{message: string}` | 发送聊天消息 |

#### 服务器 → 客户端

| 事件 | 数据 | 说明 |
|------|------|------|
| `connected` | `{status: string}` | 连接成功 |
| `user_message` | `{message: string}` | 回显用户消息 |
| `ai_response` | `{message: string}` | AI回复 |
| `tool_execution` | `{function: string, arguments: object}` | 工具执行开始 |
| `tool_result` | `{function: string, success: bool, data: object}` | 工具执行结果 |
| `error` | `{error: string}` | 错误信息 |

## 🔒 安全考虑

1. **CORS配置** - 允许跨域访问 (生产环境需限制)
2. **输入验证** - 检查消息长度和格式
3. **错误处理** - 捕获并记录所有异常
4. **资源限制** - 限制工具调用次数 (最多5次)

## 📝 自定义配置

### 修改端口
编辑 `server/app.py`:
```python
socketio.run(app, host='0.0.0.0', port=5000, debug=True)
                                       ^^^^
                                       修改端口号
```

### 修改主题色
编辑 `frontend/static/css/style.css`:
```css
:root {
    --cyber-pink: #ff006e;    /* 粉色 */
    --cyber-blue: #00f5ff;    /* 蓝色 */
    --cyber-green: #00ff9f;   /* 绿色 */
    /* ... 修改颜色值 */
}
```

## 🐛 故障排除

### 问题1: WebSocket连接失败
```
错误: WebSocket连接超时
解决: 
1. 检查Flask-SocketIO是否正确安装
2. 确认防火墙允许5000端口
3. 检查浏览器控制台错误信息
```

### 问题2: 工具执行失败
```
错误: ToolExecutor初始化失败
解决:
1. 检查七牛云API密钥配置
2. 确认macOS系统权限
3. 查看日志文件: ~/.macmind/logs/
```

### 问题3: 页面样式显示异常
```
错误: CSS文件加载失败
解决:
1. 检查frontend/static目录结构
2. 清除浏览器缓存
3. 确认Flask static_folder配置正确
```

## 📚 相关文档

- [阶段1: Function Calling实现](../README.md#阶段1)
- [API参考文档](./API_REFERENCE.md)
- [开发指南](./DEVELOPMENT.md)

## 🚧 待实现功能 (阶段3)

- [ ] 用户确认机制 (敏感操作)
- [ ] 语音输入支持
- [ ] 多会话管理
- [ ] 系统托盘集成
- [ ] 性能优化和缓存

## 📞 技术支持

遇到问题? 请在GitHub提交Issue:
https://github.com/RJ-SRE/aiAllControl/issues

---

**Version**: 2.0.0 (Phase 2)  
**Last Updated**: 2025-10-26  
**Author**: @xgopilot
