#!/usr/bin/env python3
"""
MacMind - AI 驱动的软件管理工具

命令行入口文件
"""

from controller.cli_controller import CLIController


def main():
    """
    主函数 - CLI入口
    
    功能:
        创建CLIController实例并运行
    
    使用方法:
        python macmind.py search 绘图软件
        python macmind.py install drawio
        python macmind.py list
    """
    controller = CLIController()
    controller.run()


if __name__ == '__main__':
    main()
