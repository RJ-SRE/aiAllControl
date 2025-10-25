# 🧪 MacMind 测试文档

本文档说明如何运行 MacMind 项目的测试用例。

---

## 📋 环境准备

### 1. 安装依赖

```bash
# 安装运行时依赖
pip install -r requirements.txt

# 或者使用开发模式安装（推荐）
pip install -e ".[dev]"
```

### 2. 配置环境变量（可选）

某些测试可能需要真实的 API 密钥：

```bash
# Anthropic API
export ANTHROPIC_API_KEY="your-api-key-here"

# 或 OpenAI API
export OPENAI_API_KEY="your-api-key-here"
```

**注意**：大部分测试使用 Mock，不需要真实 API 密钥。

---

## 🚀 运行测试

### 运行所有测试

```bash
pytest
```

### 运行特定测试文件

```bash
# 测试日志模块
pytest tests/test_logger.py

# 测试配置模块
pytest tests/test_config.py

# 测试 Homebrew 执行器
pytest tests/test_brew_executor.py

# 测试 AI 客户端
pytest tests/test_ai_client.py
```

### 运行特定测试类

```bash
# 测试 Logger 单例模式
pytest tests/test_logger.py::TestLoggerSingleton

# 测试配置默认值
pytest tests/test_config.py::TestConfigDefaults
```

### 运行特定测试方法

```bash
# 测试单例是否返回同一实例
pytest tests/test_logger.py::TestLoggerSingleton::test_singleton_same_instance
```

---

## 📊 测试覆盖率

### 生成覆盖率报告

```bash
# 生成终端报告
pytest --cov=infrastructure --cov-report=term

# 生成 HTML 报告
pytest --cov=infrastructure --cov-report=html

# 查看 HTML 报告
open htmlcov/index.html  # macOS
# 或
xdg-open htmlcov/index.html  # Linux
```

### 覆盖率目标

- **整体覆盖率**: ≥ 80%
- **核心模块**: ≥ 90%

---

## 🏷️ 测试标记

项目使用 pytest markers 对测试进行分类：

### 运行单元测试

```bash
pytest -m unit
```

### 运行集成测试

```bash
pytest -m integration
```

### 跳过慢速测试

```bash
pytest -m "not slow"
```

---

## 📝 测试文件说明

### `tests/test_logger.py`

测试日志模块的功能：

- ✅ 单例模式实现
- ✅ 日志文件和目录创建
- ✅ 不同级别的日志记录
- ✅ 日志格式验证

**测试类**：
- `TestLoggerSingleton`: 单例模式测试
- `TestLoggerSetup`: 日志配置测试
- `TestLoggerMethods`: 日志方法测试
- `TestLoggerOutput`: 日志输出测试
- `TestLoggerLevels`: 日志级别测试

### `tests/test_config.py`

测试配置管理模块：

- ✅ 单例模式实现
- ✅ 默认配置加载
- ✅ 配置读取和设置
- ✅ 配置文件持久化
- ✅ 环境变量优先级
- ✅ 配置验证

**测试类**：
- `TestConfigSingleton`: 单例模式测试
- `TestConfigDefaults`: 默认配置测试
- `TestConfigGetSet`: 配置读写测试
- `TestConfigPersistence`: 持久化测试
- `TestConfigValidation`: 配置验证测试
- `TestConfigEnvironmentVariables`: 环境变量测试

### `tests/test_brew_executor.py`

测试 Homebrew 命令执行器：

- ✅ 命令执行基础功能
- ✅ 搜索软件包
- ✅ 获取包信息
- ✅ 安装软件包
- ✅ 列出已安装包
- ✅ 错误处理
- ✅ 超时控制

**测试类**：
- `TestBrewExecutorInit`: 初始化测试
- `TestBrewExecutorExecute`: 命令执行测试
- `TestBrewExecutorSearch`: 搜索功能测试
- `TestBrewExecutorInfo`: 包信息测试
- `TestBrewExecutorInstall`: 安装功能测试
- `TestBrewExecutorListInstalled`: 列出已安装包测试

### `tests/test_ai_client.py`

测试 AI 客户端模块：

- ✅ 抽象基类定义
- ✅ Anthropic 客户端功能
- ✅ OpenAI 客户端功能
- ✅ 工厂函数创建客户端
- ✅ 意图分析功能
- ✅ 错误处理和降级

**测试类**：
- `TestAIClientAbstract`: 抽象类测试
- `TestAnthropicClient`: Anthropic 客户端测试
- `TestOpenAIClient`: OpenAI 客户端测试
- `TestCreateAIClient`: 工厂函数测试
- `TestAIClientIntegration`: 集成测试

---

## 🔍 测试策略

### 单元测试

每个模块都有独立的单元测试：

- **隔离性**: 使用 Mock 隔离外部依赖
- **快速**: 单元测试应该快速执行
- **全面**: 覆盖所有公开方法和边界情况

### Mock 使用

项目使用 `unittest.mock` 和 `pytest-mock` 进行 Mock：

```python
@patch('subprocess.run')
def test_example(self, mock_run):
    mock_run.return_value = Mock(stdout="output")
    # 测试代码
```

### 测试数据

- 使用临时目录进行文件操作测试
- 使用 Mock 数据避免真实 API 调用
- 环境变量通过 `monkeypatch` 模拟

---

## 🐛 调试技巧

### 查看详细输出

```bash
pytest -vv
```

### 显示 print 输出

```bash
pytest -s
```

### 进入调试器

```bash
pytest --pdb
```

### 只运行失败的测试

```bash
pytest --lf
```

---

## ✅ 持续集成

### GitHub Actions 配置示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest --cov=infrastructure
```

---

## 📚 最佳实践

### 1. 测试命名

```python
def test_<功能>_<场景>_<预期结果>():
    # 示例
    def test_search_with_keyword_returns_list():
        pass
```

### 2. 测试结构 (AAA)

```python
def test_example():
    # Arrange - 准备测试数据
    executor = BrewExecutor()
    
    # Act - 执行被测试的操作
    result = executor.search('vim')
    
    # Assert - 验证结果
    assert isinstance(result, list)
```

### 3. 测试独立性

- 每个测试应该独立运行
- 不依赖其他测试的执行顺序
- 清理测试产生的副作用

### 4. 测试覆盖率

- 正常路径（Happy Path）
- 边界条件（Edge Cases）
- 异常情况（Error Handling）

---

## 🎯 测试清单

在提交代码前，确保：

- [ ] 所有测试通过
- [ ] 新代码有对应的测试
- [ ] 测试覆盖率不降低
- [ ] 没有跳过的测试（除非有充分理由）
- [ ] 测试代码遵循命名规范

---

## 📞 获取帮助

如果遇到测试问题：

1. 查看测试输出的错误信息
2. 检查是否安装了所有依赖
3. 确认环境变量配置
4. 查看相关模块的文档注释

---

**Happy Testing! 🎉**
