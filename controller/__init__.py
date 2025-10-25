"""
控制器层 - Controller Layer

职责：
- 接收用户输入
- 解析命令和参数
- 调用Service层执行业务逻辑
- 格式化输出结果
- 处理用户交互

设计思想：MVC模式中的Controller
- Model: Domain层的Package实体
- View: CLI输出（文本格式）
- Controller: 本层，协调用户输入和业务逻辑

架构层次：
    Controller Layer (控制器层) ← 本层
        ↓
    Service Layer (业务逻辑层)
        ↓
    Repository Layer (数据访问层)
        ↓
    Domain Layer (领域模型层)
        ↓
    Infrastructure Layer (基础设施层)

Controller层的特点：
1. 薄控制器 (Thin Controller)
   - 不包含业务逻辑
   - 只负责输入输出和调用Service

2. 用户交互
   - 解析命令行参数
   - 展示结果
   - 确认提示

3. 错误处理
   - 捕获异常
   - 友好的错误提示
   - 优雅的退出

使用示例:
    from controller.cli_controller import CLIController
    
    controller = CLIController()
    controller.run()
"""
