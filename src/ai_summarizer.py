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
