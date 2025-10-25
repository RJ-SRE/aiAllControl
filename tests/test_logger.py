"""
日志模块测试 - Logger Module Tests

测试目标:
1. 单例模式是否正常工作
2. 日志文件和目录是否正确创建
3. 不同级别的日志是否正确记录
4. 日志格式是否符合预期
"""

import pytest
import logging
from pathlib import Path
from datetime import datetime
from infrastructure.logger import Logger, logger


class TestLoggerSingleton:
    """测试单例模式"""
    
    def test_singleton_same_instance(self):
        """测试多次创建返回同一实例"""
        logger1 = Logger()
        logger2 = Logger()
        assert logger1 is logger2, "应该返回同一个实例"
    
    def test_module_level_logger_is_singleton(self):
        """测试模块级logger是单例实例"""
        new_logger = Logger()
        assert logger is new_logger, "模块级logger应该是单例实例"


class TestLoggerSetup:
    """测试日志配置"""
    
    def test_log_directory_created(self):
        """测试日志目录是否创建"""
        log_dir = Path.home() / '.macmind' / 'logs'
        assert log_dir.exists(), "日志目录应该被创建"
        assert log_dir.is_dir(), "应该是目录而不是文件"
    
    def test_log_file_created(self):
        """测试日志文件是否创建"""
        logger.info("测试日志文件创建")
        
        log_dir = Path.home() / '.macmind' / 'logs'
        log_file = log_dir / f"macmind_{datetime.now().strftime('%Y%m%d')}.log"
        
        assert log_file.exists(), "日志文件应该被创建"
        assert log_file.is_file(), "应该是文件而不是目录"
    
    def test_logger_has_correct_name(self):
        """测试logger名称是否正确"""
        test_logger = Logger()
        assert test_logger.logger.name == 'MacMind', "Logger名称应该是'MacMind'"
    
    def test_logger_has_handlers(self):
        """测试logger是否配置了处理器"""
        test_logger = Logger()
        assert len(test_logger.logger.handlers) >= 2, "应该有至少2个处理器(控制台+文件)"


class TestLoggerMethods:
    """测试日志记录方法"""
    
    def test_debug_method(self):
        """测试debug方法"""
        try:
            logger.debug("这是一条DEBUG消息")
        except Exception as e:
            pytest.fail(f"debug方法应该正常工作: {e}")
    
    def test_info_method(self):
        """测试info方法"""
        try:
            logger.info("这是一条INFO消息")
        except Exception as e:
            pytest.fail(f"info方法应该正常工作: {e}")
    
    def test_warning_method(self):
        """测试warning方法"""
        try:
            logger.warning("这是一条WARNING消息")
        except Exception as e:
            pytest.fail(f"warning方法应该正常工作: {e}")
    
    def test_error_method(self):
        """测试error方法"""
        try:
            logger.error("这是一条ERROR消息")
        except Exception as e:
            pytest.fail(f"error方法应该正常工作: {e}")
    
    def test_error_method_with_exc_info(self):
        """测试error方法带异常信息"""
        try:
            raise ValueError("测试异常")
        except ValueError:
            try:
                logger.error("捕获到异常", exc_info=True)
            except Exception as e:
                pytest.fail(f"error方法应该能处理异常信息: {e}")


class TestLoggerOutput:
    """测试日志输出"""
    
    def test_log_message_in_file(self):
        """测试日志消息是否写入文件"""
        test_message = f"测试消息_{datetime.now().timestamp()}"
        logger.info(test_message)
        
        log_dir = Path.home() / '.macmind' / 'logs'
        log_file = log_dir / f"macmind_{datetime.now().strftime('%Y%m%d')}.log"
        
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
            assert test_message in log_content, "日志消息应该出现在文件中"


class TestLoggerLevels:
    """测试日志级别"""
    
    def test_logger_level_is_debug(self):
        """测试logger级别设置为DEBUG"""
        test_logger = Logger()
        assert test_logger.logger.level == logging.DEBUG, "Logger级别应该是DEBUG"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
