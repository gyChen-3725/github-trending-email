"""
邮件发送模块测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.email_sender import render_email_content, send_email


def test_render_email_content():
    """测试邮件内容渲染"""
    repos = [
        {
            'name': 'awesome-project',
            'url': 'https://github.com/user/awesome-project',
            'description': 'An awesome test project',
            'language': 'Python',
            'stars': 1234,
            'forks': 567,
            'stars_today': 89
        },
        {
            'name': 'cool-lib',
            'url': 'https://github.com/user/cool-lib',
            'description': 'A cool library',
            'language': 'JavaScript',
            'stars': 5000,
            'forks': 1000,
            'stars_today': 150
        }
    ]
    
    html_content = render_email_content(repos)
    
    # 验证返回的是字符串
    assert isinstance(html_content, str)
    
    # 验证包含HTML结构
    assert '<!DOCTYPE html>' in html_content
    assert '<html' in html_content
    
    # 验证包含项目信息
    assert 'awesome-project' in html_content
    assert 'cool-lib' in html_content
    assert 'https://github.com/user/awesome-project' in html_content
    assert 'An awesome test project' in html_content
    assert 'Python' in html_content
    assert '1234' in html_content
    assert '89' in html_content


def test_render_email_with_empty_repos():
    """测试空数据渲染"""
    repos = []
    
    html_content = render_email_content(repos)
    
    # 验证返回的是字符串
    assert isinstance(html_content, str)
    
    # 验证包含HTML结构
    assert '<!DOCTYPE html>' in html_content
    assert '<html' in html_content
