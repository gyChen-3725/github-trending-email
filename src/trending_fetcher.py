"""
GitHub trending数据获取模块
"""
import logging
import time
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 常量配置
TRENDING_URL = "https://github.com/trending"
MAX_RETRIES = 3
RETRY_DELAY = 5  # 秒
REQUEST_TIMEOUT = 30  # 秒


def fetch_trending_repos(limit: int = 10) -> List[Dict[str, str]]:
    """
    获取GitHub trending项目
    
    Args:
        limit: 获取项目数量，默认10个
        
    Returns:
        list: 项目信息列表，每个项目包含：
            - name: 项目名称（owner/repo）
            - description: 项目描述
            - url: 项目链接
            - language: 主要编程语言
            - stars: 总star数
            - stars_today: 今日新增star数
    """
    if limit <= 0:
        logger.info("limit为0，返回空列表")
        return []
    
    # 重试机制
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"正在获取trending项目数据 (尝试 {attempt + 1}/{MAX_RETRIES})")
            
            # 发送HTTP请求
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(
                TRENDING_URL,
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            # 解析HTML
            repos = _parse_trending_page(response.text, limit)
            
            logger.info(f"成功获取 {len(repos)} 个trending项目")
            return repos
            
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}")
            
            if attempt < MAX_RETRIES - 1:
                # 指数退避
                delay = RETRY_DELAY * (2 ** attempt)
                logger.info(f"等待 {delay} 秒后重试...")
                time.sleep(delay)
            else:
                logger.error("达到最大重试次数，放弃获取")
                raise
                
        except Exception as e:
            logger.error(f"解析数据时发生错误: {e}")
            raise
    
    return []


def _parse_trending_page(html_content: str, limit: int) -> List[Dict[str, str]]:
    """
    解析GitHub trending页面HTML
    
    Args:
        html_content: HTML页面内容
        limit: 返回项目数量限制
        
    Returns:
        list: 解析后的项目信息列表
    """
    soup = BeautifulSoup(html_content, 'lxml')
    repos = []
    
    # 找到所有trending项目的article元素
    articles = soup.find_all('article', class_='Box-row')
    
    for article in articles[:limit]:
        try:
            repo_info = _parse_repo_article(article)
            if repo_info:
                repos.append(repo_info)
        except Exception as e:
            logger.warning(f"解析单个项目时出错: {e}")
            continue
    
    return repos


def _parse_repo_article(article) -> Optional[Dict[str, str]]:
    """
    解析单个项目的article元素
    
    Args:
        article: BeautifulSoup元素对象
        
    Returns:
        dict: 项目信息，如果解析失败返回None
    """
    try:
        # 获取项目名称和URL
        h2 = article.find('h2', class_='h3')
        if not h2:
            return None
            
        link = h2.find('a')
        if not link:
            return None
            
        repo_path = link.get('href', '').strip()
        repo_name = repo_path.lstrip('/')
        repo_url = f"https://github.com{repo_path}"
        
        # 获取项目描述
        description_elem = article.find('p', class_='col-9')
        description = description_elem.get_text(strip=True) if description_elem else "No description"
        
        # 获取编程语言
        language_elem = article.find('span', attrs={'itemprop': 'programmingLanguage'})
        language = language_elem.get_text(strip=True) if language_elem else "Unknown"
        
        # 获取总star数
        stars_elem = article.find('svg', class_='octicon-star')
        if stars_elem:
            stars_text = stars_elem.find_next('span')
            stars = stars_text.get_text(strip=True) if stars_text else "0"
        else:
            stars = "0"
        
        # 获取今日新增star数
        stars_today = "0"
        star_spans = article.find_all('span', class_='d-inline-block')
        for span in star_spans:
            text = span.get_text(strip=True)
            if 'stars today' in text.lower() or 'star today' in text.lower():
                # 提取数字
                stars_today = text.split()[0].replace(',', '')
                break
        
        return {
            'name': repo_name,
            'description': description,
            'url': repo_url,
            'language': language,
            'stars': stars.replace(',', ''),
            'stars_today': stars_today
        }
        
    except Exception as e:
        logger.warning(f"解析项目详情时出错: {e}")
        return None
