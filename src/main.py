"""主程序入口"""
import sys
import logging
from src.trending_fetcher import fetch_trending_repos
from src.email_sender import send_email
from src.config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    try:
        logger.info("=" * 50)
        logger.info("GitHub每日趋势邮件推送系统启动")
        logger.info("=" * 50)
        
        # 验证配置
        try:
            Config.validate()
        except ValueError as e:
            logger.error(f"配置验证失败: {e}")
            logger.error("请检查环境变量配置")
            sys.exit(1)
        
        # 获取trending数据
        logger.info(f"正在获取trending项目 (限制: {Config.TRENDING_LIMIT})...")
        repos = fetch_trending_repos(limit=Config.TRENDING_LIMIT)
        
        if not repos:
            logger.error("未能获取到trending数据，程序退出")
            sys.exit(1)
        
        logger.info(f"成功获取 {len(repos)} 个项目")
        
        # AI总结增强（可选）
        if Config.ENABLE_AI_SUMMARY:
            from src.ai_summarizer import summarize_repos
            logger.info("AI总结功能已启用，开始生成项目总结...")
            repos = summarize_repos(repos)
        else:
            logger.info("AI总结功能未启用")
        
        # 发送邮件
        logger.info("正在发送邮件...")
        success = send_email(repos)
        
        if success:
            logger.info("=" * 50)
            logger.info("任务完成！邮件已发送")
            logger.info("=" * 50)
            sys.exit(0)
        else:
            logger.error("邮件发送失败")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序执行出错: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
