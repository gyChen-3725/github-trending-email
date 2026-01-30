"""配置模块测试"""
import pytest
from src.config import Config


def test_config_has_smtp_settings():
    """测试SMTP配置存在"""
    assert Config.SMTP_SERVER == 'smtp.163.com'
    assert Config.SMTP_PORT == 465


def test_config_validate_missing_email():
    """测试验证缺少邮件配置时抛出异常"""
    # 保存原始值
    original_sender = Config.EMAIL_SENDER
    original_password = Config.EMAIL_PASSWORD
    original_receiver = Config.EMAIL_RECEIVER
    
    try:
        # 设置为None以模拟缺失
        Config.EMAIL_SENDER = None
        Config.EMAIL_PASSWORD = None
        Config.EMAIL_RECEIVER = None
        
        with pytest.raises(ValueError) as exc_info:
            Config.validate()
        
        assert "缺少必要的配置项" in str(exc_info.value)
    finally:
        # 恢复原始值
        Config.EMAIL_SENDER = original_sender
        Config.EMAIL_PASSWORD = original_password
        Config.EMAIL_RECEIVER = original_receiver


def test_trending_limit_default():
    """测试Trending限制默认值"""
    assert Config.TRENDING_LIMIT == 10


def test_ai_summary_config_defaults():
    """测试AI总结配置的默认值"""
    from src.config import Config
    assert Config.ENABLE_AI_SUMMARY == False
    assert Config.AI_SUMMARY_COUNT == 5
    assert Config.AI_MAX_RETRIES == 3
    assert Config.QWEN_MODEL == 'qwen-turbo'


def test_ai_summary_validation_when_enabled(monkeypatch):
    """测试启用AI总结时必须有API Key"""
    # 先设置必要的邮件配置避免邮件验证失败
    monkeypatch.setenv('EMAIL_SENDER', 'test@example.com')
    monkeypatch.setenv('EMAIL_PASSWORD', 'test_password')
    monkeypatch.setenv('EMAIL_RECEIVER', 'receiver@example.com')
    monkeypatch.setenv('ENABLE_AI_SUMMARY', 'true')
    monkeypatch.setenv('QWEN_API_KEY', '')
    
    # 重新导入模块以应用新的环境变量
    import importlib
    import src.config
    importlib.reload(src.config)
    from src.config import Config
    
    with pytest.raises(ValueError, match='QWEN_API_KEY'):
        Config.validate()


def test_ai_summary_validation_when_disabled(monkeypatch):
    """测试禁用AI总结时不验证API Key"""
    # 先设置必要的邮件配置
    monkeypatch.setenv('EMAIL_SENDER', 'test@example.com')
    monkeypatch.setenv('EMAIL_PASSWORD', 'test_password')
    monkeypatch.setenv('EMAIL_RECEIVER', 'receiver@example.com')
    monkeypatch.setenv('ENABLE_AI_SUMMARY', 'false')
    monkeypatch.setenv('QWEN_API_KEY', '')
    
    # 重新导入模块以应用新的环境变量
    import importlib
    import src.config
    importlib.reload(src.config)
    from src.config import Config
    
    # 应该不抛出异常
    Config.validate()
