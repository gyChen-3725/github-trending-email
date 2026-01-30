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
