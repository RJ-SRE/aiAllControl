"""
性能测试 - Performance Tests

测试系统性能指标和优化效果。

测试内容:
1. 缓存命中率
2. 响应时间
3. 内存使用
4. Token估算准确性
5. 会话保存/加载性能

设计说明:
- 使用时间测量评估性能
- 使用mock避免真实API调用
- 设置性能基准(benchmark)
"""

import pytest
import time
from unittest.mock import Mock, patch
from pathlib import Path

from service.package_service import PackageService
from repository.package_repository import PackageRepository
from infrastructure.conversation import ConversationManager


class TestCachePerformance:
    """
    缓存性能测试
    
    测试缓存机制对性能的提升
    """
    
    @patch('infrastructure.brew_executor.brew.search')
    @patch('infrastructure.brew_executor.brew.info')
    def test_cache_hit_performance(self, mock_info, mock_search, tmp_path):
        """
        测试缓存命中性能
        
        验证:
        1. 首次查询较慢(需要调用API)
        2. 缓存命中后查询很快
        3. 缓存命中率符合预期
        """
        mock_search.return_value = ['vim']
        mock_info.return_value = {
            'name': 'vim',
            'desc': 'Vi IMproved',
            'version': '9.0',
            'license': 'Vim'
        }
        
        repo = PackageRepository()
        repo.cache_dir = tmp_path
        
        start = time.time()
        result1 = repo.search('vim')
        first_query_time = time.time() - start
        
        start = time.time()
        result2 = repo.search('vim')
        cached_query_time = time.time() - start
        
        assert result1 == result2
        assert cached_query_time < first_query_time
        assert mock_search.call_count == 1
        
        print(f"\n首次查询: {first_query_time*1000:.2f}ms")
        print(f"缓存查询: {cached_query_time*1000:.2f}ms")
        print(f"性能提升: {(first_query_time/cached_query_time):.1f}x")
    
    @patch('infrastructure.brew_executor.brew.info')
    def test_batch_query_performance(self, mock_info, tmp_path):
        """
        测试批量查询性能
        
        验证:
        批量查询10个软件包的性能表现
        """
        mock_info.return_value = {
            'name': 'test',
            'desc': 'Test package',
            'version': '1.0',
            'license': 'MIT'
        }
        
        repo = PackageRepository()
        repo.cache_dir = tmp_path
        
        packages = [f'package{i}' for i in range(10)]
        
        start = time.time()
        results = [repo.get_package_info(pkg) for pkg in packages]
        batch_time = time.time() - start
        
        assert len(results) == 10
        assert all(r is not None for r in results)
        
        avg_time = batch_time / 10
        print(f"\n批量查询10个包: {batch_time*1000:.2f}ms")
        print(f"平均每个包: {avg_time*1000:.2f}ms")
        
        assert avg_time < 0.1


class TestConversationPerformance:
    """
    对话管理性能测试
    
    测试会话管理的性能表现
    """
    
    def test_large_conversation_performance(self, tmp_path):
        """
        测试大量消息的性能
        
        验证:
        1. 添加100条消息的性能
        2. 获取上下文的性能
        3. 保存/加载大会话的性能
        """
        manager = ConversationManager()
        manager.session_dir = tmp_path
        manager.clear_history()
        
        start = time.time()
        for i in range(50):
            manager.add_user_message(f"用户消息 {i}")
            manager.add_assistant_message(f"AI响应 {i}")
        add_time = time.time() - start
        
        assert manager.get_message_count() == 100
        
        start = time.time()
        context = manager.get_context()
        get_context_time = time.time() - start
        
        assert len(context) <= 50
        
        start = time.time()
        manager.save_session("perf_test")
        save_time = time.time() - start
        
        manager.clear_history()
        
        start = time.time()
        manager.load_session("perf_test")
        load_time = time.time() - start
        
        print(f"\n添加100条消息: {add_time*1000:.2f}ms")
        print(f"获取上下文: {get_context_time*1000:.2f}ms")
        print(f"保存会话: {save_time*1000:.2f}ms")
        print(f"加载会话: {load_time*1000:.2f}ms")
        
        assert add_time < 0.1
        assert get_context_time < 0.01
        assert save_time < 0.1
        assert load_time < 0.1
    
    def test_token_estimation_accuracy(self):
        """
        测试Token估算的准确性
        
        验证:
        Token估算与实际使用的偏差在合理范围内
        """
        manager = ConversationManager()
        manager.clear_history()
        
        test_messages = [
            ("Hello, how are you?", 5),
            ("你好，很高兴认识你！", 12),
            ("This is a longer message with more tokens to test the estimation algorithm.", 15),
            ("这是一条包含中英文混合的消息 with mixed content.", 25)
        ]
        
        for msg, expected_min_tokens in test_messages:
            manager.clear_history()
            manager.add_user_message(msg)
            
            estimated = manager.estimate_tokens()
            
            assert estimated >= expected_min_tokens * 0.5
            assert estimated <= expected_min_tokens * 2.0
            
            print(f"\n消息: {msg[:50]}...")
            print(f"估算tokens: {estimated}")


class TestResponseTimeBaseline:
    """
    响应时间基准测试
    
    建立性能基准,用于回归测试
    """
    
    @patch('infrastructure.brew_executor.brew.search')
    def test_search_response_baseline(self, mock_search):
        """
        测试搜索响应时间基准
        
        基准: 搜索操作应在100ms内完成(mock环境)
        """
        mock_search.return_value = ['vim', 'emacs', 'nano']
        
        repo = PackageRepository()
        
        times = []
        for _ in range(10):
            start = time.time()
            repo.search('editor')
            times.append(time.time() - start)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        print(f"\n平均响应时间: {avg_time*1000:.2f}ms")
        print(f"最大响应时间: {max_time*1000:.2f}ms")
        print(f"最小响应时间: {min_time*1000:.2f}ms")
        
        assert avg_time < 0.1
        assert max_time < 0.2
    
    def test_memory_efficiency(self):
        """
        测试内存使用效率
        
        验证:
        会话管理器的内存使用在合理范围内
        """
        import sys
        
        manager = ConversationManager()
        manager.clear_history()
        
        initial_size = sys.getsizeof(manager.history)
        
        for i in range(100):
            manager.add_user_message(f"Message {i}" * 10)
        
        final_size = sys.getsizeof(manager.history)
        
        messages = manager.history
        avg_message_size = (final_size - initial_size) / len(messages) if messages else 0
        
        print(f"\n初始内存: {initial_size} bytes")
        print(f"100条消息后: {final_size} bytes")
        print(f"平均每条消息: {avg_message_size:.0f} bytes")
        
        assert final_size < 100 * 1024


class TestConcurrentOperations:
    """
    并发操作测试
    
    测试多个操作同时进行时的性能
    """
    
    def test_concurrent_cache_access(self, tmp_path):
        """
        测试并发缓存访问
        
        验证:
        多个搜索同时进行时不会相互干扰
        """
        import concurrent.futures
        
        repo = PackageRepository()
        repo.cache_dir = tmp_path
        
        keywords = ['editor', 'browser', 'terminal', 'music', 'video']
        
        with patch('infrastructure.brew_executor.brew.search') as mock_search:
            mock_search.side_effect = lambda kw: [f'{kw}1', f'{kw}2']
            
            start = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(repo.search, kw) for kw in keywords]
                results = [f.result() for f in futures]
            elapsed = time.time() - start
            
            assert len(results) == 5
            assert all(len(r) == 2 for r in results)
            
            print(f"\n并发5个搜索: {elapsed*1000:.2f}ms")
            assert elapsed < 1.0


@pytest.fixture
def performance_logger():
    """性能日志记录器"""
    print("\n" + "=" * 60)
    print("性能测试开始")
    print("=" * 60)
    yield
    print("=" * 60)
    print("性能测试完成")
    print("=" * 60)
