"""
测试GitHub trending数据获取模块
"""
import pytest
from src.trending_fetcher import fetch_trending_repos


def test_fetch_trending_returns_list():
    """测试fetch_trending_repos返回列表且长度<=5"""
    repos = fetch_trending_repos(limit=5)
    
    assert isinstance(repos, list)
    assert len(repos) <= 5
    assert len(repos) > 0  # 确保获取到了数据


def test_fetch_trending_repo_structure():
    """测试返回数据包含必需字段"""
    repos = fetch_trending_repos(limit=3)
    
    assert len(repos) > 0  # 至少有一个repo
    
    repo = repos[0]
    required_fields = ['name', 'description', 'url', 'language', 'stars', 'stars_today']
    
    for field in required_fields:
        assert field in repo, f"缺少必需字段: {field}"
    
    # 验证数据类型
    assert isinstance(repo['name'], str)
    assert isinstance(repo['url'], str)
    assert repo['url'].startswith('https://github.com/')


def test_fetch_trending_with_invalid_limit():
    """测试limit=0时返回空列表"""
    repos = fetch_trending_repos(limit=0)
    
    assert isinstance(repos, list)
    assert len(repos) == 0
