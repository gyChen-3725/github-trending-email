"""
邮件发送模块
负责邮件内容渲染和发送
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import List, Dict, Optional
from jinja2 import Environment, FileSystemLoader
from src.config import Config


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def render_email_content(repos: List[Dict]) -> str:
    """渲染邮件HTML内容
    
    Args:
        repos: 仓库列表，每个仓库包含name, url, description等字段
        
    Returns:
        str: 渲染后的HTML内容
        
    Raises:
        Exception: 模板渲染失败时
    """
    try:
        # 获取模板目录
        template_dir = Path(__file__).parent.parent / 'templates'
        
        # 创建Jinja2环境
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        
        # 加载模板
        template = env.get_template('email_template.html')
        
        # 渲染模板
        html_content = template.render(repos=repos)
        
        logger.info(f"成功渲染邮件模板，包含 {len(repos)} 个仓库")
        return html_content
        
    except Exception as e:
        logger.error(f"渲染邮件模板失败: {e}")
        raise


def send_email(repos: List[Dict], subject: Optional[str] = None) -> bool:
    """发送HTML邮件
    
    Args:
        repos: 仓库列表
        subject: 邮件主题，默认为 "GitHub每日趋势 - YYYY-MM-DD"
        
    Returns:
        bool: 发送成功返回True，失败抛出异常
        
    Raises:
        ValueError: 配置验证失败时
        Exception: 邮件发送失败时
    """
    try:
        # 验证配置
        Config.validate()
        
        # 渲染邮件内容
        html_content = render_email_content(repos)
        
        # 设置默认主题
        if subject is None:
            from datetime import datetime
            subject = f"GitHub每日趋势 - {datetime.now().strftime('%Y-%m-%d')}"
        
        # 创建MIME邮件对象
        msg = MIMEMultipart('alternative')
        msg['From'] = Config.EMAIL_SENDER
        msg['To'] = Config.EMAIL_RECEIVER
        msg['Subject'] = subject
        
        # 添加HTML内容
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # 通过SMTP_SSL发送邮件
        logger.info(f"正在连接到SMTP服务器 {Config.SMTP_SERVER}:{Config.SMTP_PORT}")
        
        with smtplib.SMTP_SSL(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
            # 登录
            logger.info(f"正在登录邮箱 {Config.EMAIL_SENDER}")
            server.login(Config.EMAIL_SENDER, Config.EMAIL_PASSWORD)
            
            # 发送邮件
            logger.info(f"正在发送邮件到 {Config.EMAIL_RECEIVER}")
            server.send_message(msg)
            
        logger.info("邮件发送成功！")
        return True
        
    except ValueError as e:
        logger.error(f"配置验证失败: {e}")
        raise
    except smtplib.SMTPException as e:
        logger.error(f"SMTP错误: {e}")
        raise Exception(f"邮件发送失败: {e}")
    except Exception as e:
        logger.error(f"发送邮件时发生错误: {e}")
        raise
