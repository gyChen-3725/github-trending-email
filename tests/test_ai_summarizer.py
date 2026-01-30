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
