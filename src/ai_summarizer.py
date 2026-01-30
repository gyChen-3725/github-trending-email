"""AI总结模块"""
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Optional, List

try:
    import dashscope
except ImportError:
    dashscope = None

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """大语言模型Provider抽象基类"""
    
    @abstractmethod
    def generate_summary(self, repo: Dict) -> Optional[str]:
        """生成单个项目的总结
        
        Args:
            repo: 项目信息字典
            
        Returns:
            str: AI生成的总结，失败返回None
        """
        pass


class QwenProvider(BaseLLMProvider):
    """通义千问Provider实现"""
    
    def __init__(self):
        """初始化Provider"""
        from src.config import Config
        self.api_key = Config.QWEN_API_KEY
        self.model = Config.QWEN_MODEL
        self.max_retries = Config.AI_MAX_RETRIES
        self.timeout = Config.AI_TIMEOUT
    
    def _build_prompt(self, repo: Dict) -> str:
        """构建Prompt模板
        
        Args:
            repo: 项目信息字典
            
        Returns:
            str: 完整的Prompt
        """
        return f"""你是一个GitHub项目分析专家。请为以下项目生成简洁的中文总结（150-200字）：

项目名称：{repo['name']}
描述：{repo['description']}
编程语言：{repo['language']}
今日新增stars：{repo['stars_today']}

请包含：
1. 项目用途和核心功能
2. 主要特点和优势
3. 适用场景
4. 技术亮点（如果明显）

用通俗易懂的语言，避免过于技术化的术语。"""
    
    def generate_summary(self, repo: Dict) -> Optional[str]:
        """生成项目总结
        
        Args:
            repo: 项目信息字典
            
        Returns:
            str: AI生成的总结，失败返回None
        """
        if dashscope is None:
            logger.error("dashscope未安装，无法生成AI总结")
            return None
            
        prompt = self._build_prompt(repo)
        
        for attempt in range(self.max_retries):
            try:
                response = dashscope.Generation.call(
                    model=self.model,
                    prompt=prompt,
                    api_key=self.api_key
                )
                
                if response.status_code == 200:
                    return response.output.text
                else:
                    logger.warning(f"API返回错误状态码: {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"AI总结失败 (尝试 {attempt+1}/{self.max_retries}): {e}")
                
            # 指数退避重试
            if attempt < self.max_retries - 1:
                sleep_time = 2 ** attempt
                time.sleep(sleep_time)
        
        return None


def summarize_repos(repos: List[Dict]) -> List[Dict]:
    """为trending项目批量生成AI总结
    
    Args:
        repos: trending项目列表
        
    Returns:
        增强后的项目列表，前N个项目新增 'ai_summary' 字段
    """
    from src.config import Config
    
    # 检查是否启用AI总结
    if not Config.ENABLE_AI_SUMMARY:
        logger.info("AI总结功能未启用，跳过")
        return repos
    
    # 确定要总结的项目数量
    count = min(Config.AI_SUMMARY_COUNT, len(repos))
    
    if count == 0:
        logger.info("没有项目需要总结")
        return repos
    
    logger.info(f"开始为前 {count} 个trending项目生成AI总结...")
    
    # 创建Provider实例
    provider = QwenProvider()
    
    # 批量处理
    success_count = 0
    for i in range(count):
        repo = repos[i]
        summary = provider.generate_summary(repo)
        
        if summary:
            repo['ai_summary'] = summary
            success_count += 1
        else:
            repo['ai_summary'] = None
            logger.warning(f"项目 {repo['name']} 总结失败，将使用原始描述")
    
    logger.info(f"AI总结完成：{success_count}/{count} 个项目成功")
    return repos
