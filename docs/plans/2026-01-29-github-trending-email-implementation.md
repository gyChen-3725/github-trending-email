# GitHub每日趋势邮件推送系统 实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建一个自动化系统，每天早上8点通过GitHub Actions获取GitHub trending前10个项目并发送到163邮箱

**Architecture:** Python脚本 + GitHub Actions定时任务。脚本调用trending API获取数据，使用Jinja2渲染HTML邮件模板，通过SMTP发送到163邮箱。

**Tech Stack:** Python 3.11+, requests, jinja2, smtplib, GitHub Actions

---

## Task 1: 项目基础结构搭建

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `README.md`

**Step 1: 创建Python依赖文件**

创建 `requirements.txt`:

```txt
requests>=2.31.0
jinja2>=3.1.0
python-dotenv>=1.0.0
beautifulsoup4>=4.12.0
```

**Step 2: 创建环境变量示例文件**

创建 `.env.example`:

```env
# 163邮箱配置
EMAIL_SENDER=your_email@163.com
EMAIL_PASSWORD=your_smtp_authorization_code
EMAIL_RECEIVER=your_email@163.com

# Trending配置
TRENDING_LIMIT=10
```

**Step 3: 创建README文档**

创建 `README.md`:

```markdown
# GitHub每日趋势邮件推送

每天自动获取GitHub trending项目并发送邮件通知。

## 功能特性

- 每天早上8点（北京时间）自动执行
- 获取GitHub trending前10个项目
- 精美的HTML邮件格式
- 通过GitHub Actions自动运行

## 本地测试

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
```bash
cp .env.example .env
# 编辑.env文件，填入你的163邮箱配置
```

3. 运行测试：
```bash
python src/main.py
```

## GitHub Actions部署

1. Fork本仓库
2. 在仓库Settings → Secrets中添加：
   - `EMAIL_SENDER`: 发送邮箱
   - `EMAIL_PASSWORD`: 163邮箱SMTP授权码
   - `EMAIL_RECEIVER`: 接收邮箱
3. 定时任务将自动运行

## 163邮箱SMTP配置

1. 登录163邮箱
2. 设置 → POP3/SMTP/IMAP
3. 开启SMTP服务
4. 获取授权码（不是登录密码）
```

**Step 4: 提交基础结构**

```bash
git add requirements.txt .env.example README.md
git commit -m "chore: 添加项目基础结构和文档"
```

---

## Task 2: 配置管理模块

**Files:**
- Create: `src/config.py`
- Create: `src/__init__.py`

**Step 1: 创建src目录的__init__.py**

创建 `src/__init__.py`:

```python
"""GitHub每日趋势邮件推送系统"""
```

**Step 2: 编写配置管理模块**

创建 `src/config.py`:

```python
"""配置管理模块"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """系统配置"""
    
    # 邮件配置
    EMAIL_SENDER = os.getenv('EMAIL_SENDER', '')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
    EMAIL_RECEIVER = os.getenv('EMAIL_RECEIVER', '')
    
    # SMTP配置
    SMTP_SERVER = 'smtp.163.com'
    SMTP_PORT = 465  # SSL端口
    
    # Trending配置
    TRENDING_LIMIT = int(os.getenv('TRENDING_LIMIT', '10'))
    
    @classmethod
    def validate(cls):
        """验证必要的配置项"""
        required = ['EMAIL_SENDER', 'EMAIL_PASSWORD', 'EMAIL_RECEIVER']
        missing = [key for key in required if not getattr(cls, key)]
        
        if missing:
            raise ValueError(f"缺少必要的配置项: {', '.join(missing)}")
        
        return True
```

**Step 3: 编写配置模块测试**

创建 `tests/__init__.py`:

```python
"""测试模块"""
```

创建 `tests/test_config.py`:

```python
"""测试配置模块"""
import os
import pytest
from src.config import Config

def test_config_has_smtp_settings():
    """测试SMTP配置"""
    assert Config.SMTP_SERVER == 'smtp.163.com'
    assert Config.SMTP_PORT == 465

def test_config_validate_missing_email():
    """测试配置验证 - 缺少邮箱配置"""
    # 保存原始值
    original_sender = Config.EMAIL_SENDER
    original_password = Config.EMAIL_PASSWORD
    original_receiver = Config.EMAIL_RECEIVER
    
    try:
        # 清空配置
        Config.EMAIL_SENDER = ''
        Config.EMAIL_PASSWORD = ''
        Config.EMAIL_RECEIVER = ''
        
        # 应该抛出异常
        with pytest.raises(ValueError) as exc_info:
            Config.validate()
        
        assert '缺少必要的配置项' in str(exc_info.value)
    finally:
        # 恢复原始值
        Config.EMAIL_SENDER = original_sender
        Config.EMAIL_PASSWORD = original_password
        Config.EMAIL_RECEIVER = original_receiver

def test_trending_limit_default():
    """测试trending限制默认值"""
    assert Config.TRENDING_LIMIT == 10
```

**Step 4: 运行测试**

```bash
pip install pytest
pytest tests/test_config.py -v
```

预期: 3个测试通过

**Step 5: 提交配置模块**

```bash
git add src/config.py src/__init__.py tests/__init__.py tests/test_config.py
git commit -m "feat: 添加配置管理模块"
```

---

## Task 3: Trending数据获取模块

**Files:**
- Create: `src/trending_fetcher.py`
- Create: `tests/test_trending_fetcher.py`

**Step 1: 编写trending获取模块的测试**

创建 `tests/test_trending_fetcher.py`:

```python
"""测试trending获取模块"""
import pytest
from src.trending_fetcher import fetch_trending_repos

def test_fetch_trending_returns_list():
    """测试返回列表"""
    repos = fetch_trending_repos(limit=5)
    assert isinstance(repos, list)
    assert len(repos) <= 5

def test_fetch_trending_repo_structure():
    """测试返回的项目数据结构"""
    repos = fetch_trending_repos(limit=1)
    
    if len(repos) > 0:
        repo = repos[0]
        required_fields = ['name', 'description', 'url', 'language', 'stars', 'stars_today']
        
        for field in required_fields:
            assert field in repo, f"缺少字段: {field}"

def test_fetch_trending_with_invalid_limit():
    """测试无效的限制参数"""
    repos = fetch_trending_repos(limit=0)
    assert repos == []
```

**Step 2: 运行测试确认失败**

```bash
pytest tests/test_trending_fetcher.py -v
```

预期: 失败，提示模块不存在

**Step 3: 实现trending获取模块**

创建 `src/trending_fetcher.py`:

```python
"""GitHub Trending数据获取模块"""
import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_trending_repos(limit: int = 10) -> List[Dict]:
    """
    获取GitHub trending项目
    
    Args:
        limit: 获取项目数量
        
    Returns:
        项目列表，每个项目包含：name, description, url, language, stars, stars_today
    """
    if limit <= 0:
        return []
    
    url = 'https://github.com/trending'
    repos = []
    
    # 重试机制
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(f"正在获取GitHub trending数据 (尝试 {attempt + 1}/{max_retries})...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('article', class_='Box-row')
            
            for article in articles[:limit]:
                try:
                    # 项目名称和链接
                    h2 = article.find('h2')
                    if not h2:
                        continue
                    
                    link = h2.find('a')
                    if not link:
                        continue
                    
                    repo_name = link.get('href', '').strip('/')
                    repo_url = f"https://github.com/{repo_name}"
                    
                    # 项目描述
                    desc_p = article.find('p', class_='col-9')
                    description = desc_p.get_text(strip=True) if desc_p else '无描述'
                    
                    # 编程语言
                    lang_span = article.find('span', itemprop='programmingLanguage')
                    language = lang_span.get_text(strip=True) if lang_span else 'Unknown'
                    
                    # Star数据
                    star_spans = article.find_all('span', class_='d-inline-block')
                    stars = '0'
                    stars_today = '0'
                    
                    for span in star_spans:
                        text = span.get_text(strip=True)
                        if 'stars today' in text.lower() or 'starred today' in text.lower():
                            stars_today = text.split()[0].replace(',', '')
                        elif text and text[0].isdigit():
                            stars = text.replace(',', '')
                    
                    repos.append({
                        'name': repo_name,
                        'description': description,
                        'url': repo_url,
                        'language': language,
                        'stars': stars,
                        'stars_today': stars_today
                    })
                    
                except Exception as e:
                    logger.warning(f"解析项目数据时出错: {e}")
                    continue
            
            logger.info(f"成功获取 {len(repos)} 个trending项目")
            return repos
            
        except requests.RequestException as e:
            logger.warning(f"请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(5 * (attempt + 1))  # 指数退避
            else:
                logger.error("达到最大重试次数，获取失败")
                return []
        except Exception as e:
            logger.error(f"发生未预期的错误: {e}")
            return []
    
    return repos
```

**Step 4: 运行测试**

```bash
pytest tests/test_trending_fetcher.py -v
```

预期: 3个测试通过（需要网络连接）

**Step 5: 提交trending获取模块**

```bash
git add src/trending_fetcher.py tests/test_trending_fetcher.py
git commit -m "feat: 添加GitHub trending数据获取模块"
```

---

## Task 4: 邮件模板

**Files:**
- Create: `templates/email_template.html`

**Step 1: 创建HTML邮件模板**

创建 `templates/email_template.html`:

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitHub每日趋势</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #24292e;
            background-color: #f6f8fa;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 28px;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
        }
        .content {
            padding: 30px;
        }
        .repo-card {
            background-color: #f6f8fa;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 20px;
            transition: transform 0.2s;
        }
        .repo-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .repo-rank {
            display: inline-block;
            background-color: #667eea;
            color: white;
            font-weight: bold;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 14px;
            margin-right: 10px;
        }
        .repo-name {
            font-size: 20px;
            font-weight: 600;
            color: #0366d6;
            text-decoration: none;
            display: inline-block;
        }
        .repo-name:hover {
            text-decoration: underline;
        }
        .repo-description {
            color: #586069;
            margin: 10px 0;
            font-size: 14px;
        }
        .repo-meta {
            display: flex;
            align-items: center;
            gap: 20px;
            font-size: 14px;
            color: #586069;
        }
        .language {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .language-color {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background-color: #f1e05a;
        }
        .stars {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .stars-today {
            display: flex;
            align-items: center;
            gap: 5px;
            color: #28a745;
            font-weight: 600;
        }
        .footer {
            background-color: #f6f8fa;
            padding: 20px;
            text-align: center;
            color: #586069;
            font-size: 12px;
        }
        @media (max-width: 600px) {
            .container {
                margin: 0;
                border-radius: 0;
            }
            .repo-meta {
                flex-direction: column;
                align-items: flex-start;
                gap: 8px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌟 GitHub每日趋势</h1>
            <p>{{ date }}</p>
        </div>
        
        <div class="content">
            {% for repo in repos %}
            <div class="repo-card">
                <div>
                    <span class="repo-rank">#{{ loop.index }}</span>
                    <a href="{{ repo.url }}" class="repo-name">{{ repo.name }}</a>
                </div>
                
                <div class="repo-description">
                    {{ repo.description }}
                </div>
                
                <div class="repo-meta">
                    <div class="language">
                        <span class="language-color"></span>
                        <span>{{ repo.language }}</span>
                    </div>
                    <div class="stars">
                        <span>⭐</span>
                        <span>{{ repo.stars }} stars</span>
                    </div>
                    <div class="stars-today">
                        <span>📈</span>
                        <span>+{{ repo.stars_today }} stars today</span>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <div class="footer">
            <p>数据来源: GitHub Trending</p>
            <p>自动发送于 {{ timestamp }}</p>
        </div>
    </div>
</body>
</html>
```

**Step 2: 提交邮件模板**

```bash
git add templates/email_template.html
git commit -m "feat: 添加HTML邮件模板"
```

---

## Task 5: 邮件发送模块

**Files:**
- Create: `src/email_sender.py`
- Create: `tests/test_email_sender.py`

**Step 1: 编写邮件发送模块的测试**

创建 `tests/test_email_sender.py`:

```python
"""测试邮件发送模块"""
import pytest
from src.email_sender import render_email_content

def test_render_email_content():
    """测试邮件内容渲染"""
    repos = [
        {
            'name': 'test/repo',
            'description': 'Test repository',
            'url': 'https://github.com/test/repo',
            'language': 'Python',
            'stars': '1000',
            'stars_today': '100'
        }
    ]
    
    html = render_email_content(repos)
    
    assert 'GitHub每日趋势' in html
    assert 'test/repo' in html
    assert 'Test repository' in html
    assert 'Python' in html

def test_render_email_with_empty_repos():
    """测试空数据渲染"""
    html = render_email_content([])
    assert 'GitHub每日趋势' in html
```

**Step 2: 运行测试确认失败**

```bash
pytest tests/test_email_sender.py -v
```

预期: 失败，模块不存在

**Step 3: 实现邮件发送模块**

创建 `src/email_sender.py`:

```python
"""邮件发送模块"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from jinja2 import Template
from datetime import datetime
import logging
from typing import List, Dict
import os

from src.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def render_email_content(repos: List[Dict]) -> str:
    """
    渲染邮件HTML内容
    
    Args:
        repos: 项目数据列表
        
    Returns:
        HTML内容字符串
    """
    template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'email_template.html')
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    template = Template(template_content)
    
    html = template.render(
        repos=repos,
        date=datetime.now().strftime('%Y年%m月%d日'),
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    
    return html

def send_email(repos: List[Dict], subject: str = None) -> bool:
    """
    发送trending项目邮件
    
    Args:
        repos: 项目数据列表
        subject: 邮件主题（可选）
        
    Returns:
        发送是否成功
    """
    try:
        # 验证配置
        Config.validate()
        
        # 渲染邮件内容
        html_content = render_email_content(repos)
        
        # 创建邮件
        message = MIMEMultipart('alternative')
        message['From'] = Header(f"GitHub Trending <{Config.EMAIL_SENDER}>", 'utf-8')
        message['To'] = Header(Config.EMAIL_RECEIVER, 'utf-8')
        
        if subject is None:
            subject = f"🌟 GitHub每日趋势 - {datetime.now().strftime('%Y-%m-%d')}"
        message['Subject'] = Header(subject, 'utf-8')
        
        # 添加HTML内容
        html_part = MIMEText(html_content, 'html', 'utf-8')
        message.attach(html_part)
        
        # 连接SMTP服务器并发送
        logger.info(f"正在连接到SMTP服务器: {Config.SMTP_SERVER}:{Config.SMTP_PORT}")
        
        with smtplib.SMTP_SSL(Config.SMTP_SERVER, Config.SMTP_PORT, timeout=30) as server:
            logger.info("正在登录...")
            server.login(Config.EMAIL_SENDER, Config.EMAIL_PASSWORD)
            
            logger.info(f"正在发送邮件到: {Config.EMAIL_RECEIVER}")
            server.send_message(message)
            
        logger.info("邮件发送成功!")
        return True
        
    except ValueError as e:
        logger.error(f"配置错误: {e}")
        return False
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP认证失败，请检查邮箱地址和授权码")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP错误: {e}")
        return False
    except Exception as e:
        logger.error(f"发送邮件时发生错误: {e}")
        return False
```

**Step 4: 运行测试**

```bash
pytest tests/test_email_sender.py -v
```

预期: 2个测试通过

**Step 5: 提交邮件发送模块**

```bash
git add src/email_sender.py tests/test_email_sender.py
git commit -m "feat: 添加邮件发送模块"
```

---

## Task 6: 主程序入口

**Files:**
- Create: `src/main.py`

**Step 1: 编写主程序**

创建 `src/main.py`:

```python
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
        
        # 获取trending数据
        logger.info(f"正在获取trending项目 (限制: {Config.TRENDING_LIMIT})...")
        repos = fetch_trending_repos(limit=Config.TRENDING_LIMIT)
        
        if not repos:
            logger.error("未能获取到trending数据，程序退出")
            sys.exit(1)
        
        logger.info(f"成功获取 {len(repos)} 个项目")
        
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
```

**Step 2: 提交主程序**

```bash
git add src/main.py
git commit -m "feat: 添加主程序入口"
```

---

## Task 7: GitHub Actions工作流

**Files:**
- Create: `.github/workflows/daily-trending.yml`

**Step 1: 创建GitHub Actions工作流**

创建 `.github/workflows/daily-trending.yml`:

```yaml
name: GitHub Daily Trending Email

on:
  # 定时触发：每天UTC 0:00（北京时间8:00）
  schedule:
    - cron: '0 0 * * *'
  
  # 支持手动触发
  workflow_dispatch:

jobs:
  send-trending-email:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout代码
        uses: actions/checkout@v4
      
      - name: 设置Python环境
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: 安装依赖
        run: |
          pip install -r requirements.txt
      
      - name: 运行trending邮件推送
        env:
          EMAIL_SENDER: ${{ secrets.EMAIL_SENDER }}
          EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
          EMAIL_RECEIVER: ${{ secrets.EMAIL_RECEIVER }}
          TRENDING_LIMIT: 10
        run: |
          python src/main.py
      
      - name: 发送失败通知
        if: failure()
        run: |
          echo "❌ Trending邮件发送失败，请检查日志"
```

**Step 2: 提交GitHub Actions配置**

```bash
git add .github/workflows/daily-trending.yml
git commit -m "feat: 添加GitHub Actions定时任务配置"
```

---

## Task 8: 完善README和测试

**Files:**
- Modify: `README.md`

**Step 1: 更新README文档**

在 `README.md` 中添加更详细的说明：

```markdown
# GitHub每日趋势邮件推送

每天自动获取GitHub trending项目并发送邮件通知。

## 功能特性

- ✅ 每天早上8点（北京时间）自动执行
- ✅ 获取GitHub trending前10个项目（所有语言）
- ✅ 精美的HTML邮件格式
- ✅ 通过GitHub Actions自动运行，完全免费
- ✅ 支持本地测试
- ✅ 错误重试和日志记录

## 效果预览

邮件包含以下信息：
- 项目排名
- 项目名称（可点击跳转）
- 项目描述
- 编程语言
- 总star数
- 今日新增star数

## 快速开始

### 1. Fork仓库

点击右上角Fork按钮，将仓库fork到你的账号下

### 2. 配置GitHub Secrets

在你fork的仓库中，进入 `Settings` → `Secrets and variables` → `Actions`，点击 `New repository secret` 添加以下配置：

| Secret名称 | 说明 | 示例 |
|-----------|------|------|
| `EMAIL_SENDER` | 发送邮箱（163邮箱） | `your_email@163.com` |
| `EMAIL_PASSWORD` | SMTP授权码 | `ABCDEFGHIJKLMNOP` |
| `EMAIL_RECEIVER` | 接收邮箱 | `your_email@163.com` |

### 3. 获取163邮箱SMTP授权码

1. 登录 [163邮箱](https://mail.163.com)
2. 进入 `设置` → `POP3/SMTP/IMAP`
3. 开启 `SMTP服务`
4. 点击 `授权码管理`，新增授权码
5. 复制生成的授权码（注意不是邮箱登录密码！）

### 4. 启用Actions

1. 进入仓库的 `Actions` 标签
2. 点击 `I understand my workflows, go ahead and enable them`
3. 找到 `GitHub Daily Trending Email` workflow
4. 点击 `Enable workflow`

### 5. 测试运行

点击 `Run workflow` 手动触发一次，测试是否配置正确。

## 本地开发

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

```bash
cp .env.example .env
# 编辑.env文件，填入你的163邮箱配置
```

### 运行程序

```bash
python src/main.py
```

### 运行测试

```bash
pip install pytest
pytest tests/ -v
```

## 项目结构

```
.
├── .github/
│   └── workflows/
│       └── daily-trending.yml    # GitHub Actions配置
├── src/
│   ├── __init__.py
│   ├── main.py                   # 主程序
│   ├── config.py                 # 配置管理
│   ├── trending_fetcher.py       # Trending获取
│   └── email_sender.py           # 邮件发送
├── templates/
│   └── email_template.html       # 邮件模板
├── tests/                        # 测试文件
├── requirements.txt              # Python依赖
├── .env.example                  # 环境变量示例
└── README.md                     # 项目说明
```

## 技术栈

- **Python 3.11+**
- **requests** - HTTP请求
- **BeautifulSoup4** - HTML解析
- **Jinja2** - 模板引擎
- **python-dotenv** - 环境变量管理
- **GitHub Actions** - 自动化运行

## 常见问题

### 1. 为什么收不到邮件？

- 检查GitHub Secrets配置是否正确
- 确认使用的是SMTP授权码，不是登录密码
- 查看Actions运行日志，确认是否有错误

### 2. 如何修改发送时间？

编辑 `.github/workflows/daily-trending.yml` 中的 `cron` 表达式：

```yaml
schedule:
  - cron: '0 0 * * *'  # UTC 0:00，即北京时间8:00
```

### 3. 如何修改项目数量？

修改工作流中的 `TRENDING_LIMIT` 环境变量，或在GitHub Secrets中添加 `TRENDING_LIMIT`。

### 4. 邮件发送失败怎么办？

GitHub Actions会在失败时发送通知邮件。查看Actions日志了解详细错误信息。

## 开源协议

MIT License

## 贡献

欢迎提交Issue和Pull Request！
```

**Step 2: 提交更新**

```bash
git add README.md
git commit -m "docs: 完善README文档"
```

---

## Task 9: 最终测试和验证

**Step 1: 运行所有测试**

```bash
pytest tests/ -v
```

预期: 所有测试通过

**Step 2: 本地完整测试（需要配置.env）**

```bash
# 创建.env文件并填入真实配置
cp .env.example .env
# 编辑.env文件

# 运行程序
python src/main.py
```

预期: 
- 成功获取trending数据
- 成功发送邮件
- 收到邮件

**Step 3: 检查文件完整性**

```bash
ls -R
```

确认所有文件都已创建

**Step 4: 最终提交**

```bash
git status
git add .
git commit -m "chore: 完成GitHub每日趋势邮件推送系统"
```

---

## 完成检查清单

- [ ] requirements.txt 已创建
- [ ] .env.example 已创建
- [ ] src/config.py 配置模块完成
- [ ] src/trending_fetcher.py 数据获取模块完成
- [ ] src/email_sender.py 邮件发送模块完成
- [ ] src/main.py 主程序完成
- [ ] templates/email_template.html 邮件模板完成
- [ ] .github/workflows/daily-trending.yml GitHub Actions配置完成
- [ ] README.md 文档完善
- [ ] 所有测试通过
- [ ] 本地测试成功
- [ ] 代码已提交到feature分支

## 部署步骤（用户手册）

1. 将feature分支合并到main分支
2. 推送到GitHub
3. 在GitHub仓库Settings中配置Secrets
4. 启用GitHub Actions
5. 手动触发测试
6. 等待每天自动执行

---

**实现计划完成！**
