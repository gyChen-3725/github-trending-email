"""AI总结模块测试"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict


def test_base_provider_is_abstract():
    """测试BaseLLMProvider是抽象类"""
    from src.ai_summarizer import BaseLLMProvider
    
    with pytest.raises(TypeError):
        BaseLLMProvider()


def test_qwen_provider_instantiation():
    """测试QwenProvider可以实例化"""
    from src.ai_summarizer import QwenProvider
    
    provider = QwenProvider()
    assert provider is not None


@patch('src.ai_summarizer.dashscope')
def test_qwen_provider_success(mock_dashscope):
    """测试成功调用通义千问API"""
    from src.ai_summarizer import QwenProvider
    
    # Mock成功响应
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.output.text = "这是一个Python Web框架，提供高性能异步处理能力。"
    mock_dashscope.Generation.call.return_value = mock_response
    
    provider = QwenProvider()
    repo = {
        'name': 'fastapi/fastapi',
        'description': 'FastAPI framework',
        'language': 'Python',
        'stars_today': '123'
    }
    
    summary = provider.generate_summary(repo)
    
    assert summary == "这是一个Python Web框架，提供高性能异步处理能力。"
    assert mock_dashscope.Generation.call.called


@patch('src.ai_summarizer.dashscope')
@patch('src.ai_summarizer.time.sleep')
def test_qwen_provider_retry_on_failure(mock_sleep, mock_dashscope):
    """测试API失败时的重试机制"""
    from src.ai_summarizer import QwenProvider
    
    # 第1次失败，第2次成功
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.output.text = "成功的总结"
    
    mock_dashscope.Generation.call.side_effect = [
        Exception("Network error"),
        mock_response
    ]
    
    provider = QwenProvider()
    repo = {'name': 'test', 'description': 'test', 'language': 'Python', 'stars_today': '10'}
    
    summary = provider.generate_summary(repo)
    
    assert summary == "成功的总结"
    assert mock_dashscope.Generation.call.call_count == 2
    assert mock_sleep.call_count == 1  # 第1次失败后sleep


@patch('src.ai_summarizer.dashscope')
@patch('src.ai_summarizer.time.sleep')
def test_qwen_provider_all_retries_fail(mock_sleep, mock_dashscope):
    """测试所有重试都失败后返回None"""
    from src.ai_summarizer import QwenProvider
    
    mock_dashscope.Generation.call.side_effect = Exception("API Error")
    
    provider = QwenProvider()
    repo = {'name': 'test', 'description': 'test', 'language': 'Python', 'stars_today': '10'}
    
    summary = provider.generate_summary(repo)
    
    assert summary is None
    assert mock_dashscope.Generation.call.call_count == 3
    assert mock_sleep.call_count == 2  # 前2次失败后sleep


@patch('src.ai_summarizer.QwenProvider')
def test_summarize_repos_only_first_n(mock_provider_class, monkeypatch):
    """测试只总结前5个项目"""
    # 启用AI总结
    monkeypatch.setenv('ENABLE_AI_SUMMARY', 'true')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')
    
    # 重新加载config
    import importlib
    from src import config
    importlib.reload(config)
    
    from src.ai_summarizer import summarize_repos
    
    # Mock provider实例
    mock_provider = Mock()
    mock_provider.generate_summary.return_value = "AI总结内容"
    mock_provider_class.return_value = mock_provider
    
    # 创建10个项目
    repos = [
        {'name': f'repo{i}', 'description': 'test', 'language': 'Python', 'stars_today': '10'}
        for i in range(10)
    ]
    
    result = summarize_repos(repos)
    
    # 应该调用5次
    assert mock_provider.generate_summary.call_count == 5
    
    # 前5个有ai_summary
    for i in range(5):
        assert result[i]['ai_summary'] == "AI总结内容"
    
    # 后5个没有ai_summary
    for i in range(5, 10):
        assert 'ai_summary' not in result[i]


@patch('src.ai_summarizer.QwenProvider')
def test_summarize_repos_handles_partial_failure(mock_provider_class, monkeypatch):
    """测试部分项目总结失败的情况"""
    # 启用AI总结
    monkeypatch.setenv('ENABLE_AI_SUMMARY', 'true')
    monkeypatch.setenv('QWEN_API_KEY', 'test-key')
    
    # 重新加载config
    import importlib
    from src import config
    importlib.reload(config)
    
    from src.ai_summarizer import summarize_repos
    
    mock_provider = Mock()
    # 第1个成功，第2个失败，第3个成功
    mock_provider.generate_summary.side_effect = [
        "总结1",
        None,  # 失败
        "总结3",
        "总结4",
        "总结5"
    ]
    mock_provider_class.return_value = mock_provider
    
    repos = [{'name': f'repo{i}'} for i in range(5)]
    
    result = summarize_repos(repos)
    
    assert result[0]['ai_summary'] == "总结1"
    assert result[1]['ai_summary'] is None
    assert result[2]['ai_summary'] == "总结3"


def test_summarize_repos_when_disabled(monkeypatch):
    """测试禁用AI总结时直接返回"""
    monkeypatch.setenv('ENABLE_AI_SUMMARY', 'false')
    
    # 重新加载config以应用新的环境变量
    import importlib
    from src import config
    importlib.reload(config)
    
    from src.ai_summarizer import summarize_repos
    
    repos = [{'name': 'test'}]
    result = summarize_repos(repos)
    
    # 不应添加ai_summary字段
    assert 'ai_summary' not in result[0]
