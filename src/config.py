"""配置管理模块"""
import os
from typing import Optional


class Config:
    """系统配置类"""
    
    # 邮件配置
    EMAIL_SENDER: Optional[str] = os.getenv('EMAIL_SENDER')
    EMAIL_PASSWORD: Optional[str] = os.getenv('EMAIL_PASSWORD')
    EMAIL_RECEIVER: Optional[str] = os.getenv('EMAIL_RECEIVER')
    
    # SMTP配置
    SMTP_SERVER: str = 'smtp.163.com'
    SMTP_PORT: int = 465
    
    # Trending配置
    TRENDING_LIMIT: int = int(os.getenv('TRENDING_LIMIT', '10'))
    
    @classmethod
    def validate(cls) -> None:
        """验证必要的配置项
        
        Raises:
            ValueError: 当必要配置项缺失时
        """
        required_fields = {
            'EMAIL_SENDER': cls.EMAIL_SENDER,
            'EMAIL_PASSWORD': cls.EMAIL_PASSWORD,
            'EMAIL_RECEIVER': cls.EMAIL_RECEIVER
        }
        
        missing_fields = [
            field for field, value in required_fields.items() 
            if not value
        ]
        
        if missing_fields:
            raise ValueError(
                f"缺少必要的配置项: {', '.join(missing_fields)}"
            )
