# AI总结功能实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为GitHub trending项目添加通义千问AI总结功能，支持前5个项目生成详细中文解析

**Architecture:** 创建可扩展的LLM Provider抽象层，集成通义千问API，修改主流程支持可选AI增强，更新邮件模板展示AI总结

**Tech Stack:** Python 3.11+, dashscope SDK, Jinja2 templates, pytest with mocking

---

## Task 1: 配置管理扩展

**Files:**
- Modify: `src/config.py`
- Modify: `.env.example`
- Test: `tests/test_config.py`

### Step 1: 写配置扩展的失败测试

在 `tests/test_config.py` 添加：

```python
def test_ai_summary_config_defaults():
    """测试AI总结配置的默认值"""
    from src.config import Config
    assert Config.ENABLE_AI_SUMMARY == False
    assert Config.AI_SUMMARY_COUNT == 5
    assert Config.AI_MAX_RETRIES == 3
    assert Config.QWEN_MODEL == 'qwen-turbo'

def test_ai_summary_validation_when_enabled(monkeypatch):
    """测试启用AI总结时必须有API Key"""
    from src.config import Config
    monkeypatch.setenv('ENABLE_AI_SUMMARY', 'true')
    monkeypatch.setenv('QWEN_API_KEY', '')
    
    with pytest.raises(ValueError, match='QWEN_API_KEY'):
        Config.validate()

def test_ai_summary_validation_when_disabled(monkeypatch):
    """测试禁用AI总结时不验证API Key"""
    from src.config import Config
    monkeypatch.setenv('ENABLE_AI_SUMMARY', 'false')
    monkeypatch.setenv('QWEN_API_KEY', '')
    
    # 应该不抛出异常
    Config.validate()
```

### Step 2: 运行测试验证失败

运行：`python -m pytest tests/test_config.py::test_ai_summary_config_defaults -v`

预期：FAIL - 属性不存在

### Step 3: 实现Config扩展

在 `src/config.py` 添加配置项（在 `TRENDING_LIMIT` 后面）：

```python
    # AI总结功能配置
    ENABLE_AI_SUMMARY = os.getenv('ENABLE_AI_SUMMARY', 'false').lower() == 'true'
    QWEN_API_KEY = os.getenv('QWEN_API_KEY', '')
    QWEN_MODEL = os.getenv('QWEN_MODEL', 'qwen-turbo')
    AI_SUMMARY_COUNT = int(os.getenv('AI_SUMMARY_COUNT', '5'))
    AI_MAX_RETRIES = int(os.getenv('AI_MAX_RETRIES', '3'))
    AI_TIMEOUT = int(os.getenv('AI_TIMEOUT', '30'))
```

修改 `validate()` 方法，在现有验证逻辑后添加：

```python
        # 验证AI总结配置
        if cls.ENABLE_AI_SUMMARY and not cls.QWEN_API_KEY:
            raise ValueError("启用AI总结功能时必须设置 QWEN_API_KEY 环境变量")
```

### Step 4: 运行测试验证通过

运行：`python -m pytest tests/test_config.py -v`

预期：所有测试通过

### Step 5: 更新.env.example

在 `.env.example` 末尾添加：

```bash
# === AI总结配置 (可选) ===
ENABLE_AI_SUMMARY=false
QWEN_API_KEY=sk-your-qwen-api-key-here
QWEN_MODEL=qwen-turbo
AI_SUMMARY_COUNT=5
AI_MAX_RETRIES=3
AI_TIMEOUT=30
```

### Step 6: 提交

```bash
git add src/config.py tests/test_config.py .env.example
git commit -m "feat: 添加AI总结功能配置项"
```

---

## Task 2: AI总结模块 - 抽象层

**Files:**
- Create: `src/ai_summarizer.py`
- Create: `tests/test_ai_summarizer.py`

### Step 1: 写Provider接口测试

创建 `tests/test_ai_summarizer.py`：

```python
"""AI总结模块测试"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict


def test_base_provider_is_abstract():
    """测试BaseLLMProvider是抽象类"""
    from src.ai_summarizer import BaseLLMProvider
    
    with pytest.raises(TypeError):
        BaseLLMProvider()


def test_qwen_provider_instantiation():
    """测试QwenProvider可以实例化"""
    from src.ai_summarizer import QwenProvider
    
    provider = QwenProvider()
    assert provider is not None
```

### Step 2: 运行测试验证失败

运行：`python -m pytest tests/test_ai_summarizer.py::test_base_provider_is_abstract -v`

预期：FAIL - 模块不存在

### Step 3: 实现Provider抽象层

创建 `src/ai_summarizer.py`：

```python
"""AI总结模块"""
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Optional, List

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
    
    def generate_summary(self, repo: Dict) -> Optional[str]:
        """生成项目总结（暂时返回None，下一步实现）"""
        return None
```

### Step 4: 运行测试验证通过

运行：`python -m pytest tests/test_ai_summarizer.py -v`

预期：2个测试通过

### Step 5: 提交

```bash
git add src/ai_summarizer.py tests/test_ai_summarizer.py
git commit -m "feat: 添加LLM Provider抽象层"
```

---

## Task 3: 通义千问API集成

**Files:**
- Modify: `src/ai_summarizer.py`
- Modify: `tests/test_ai_summarizer.py`
- Modify: `requirements.txt`

### Step 1: 写API调用测试

在 `tests/test_ai_summarizer.py` 添加：

```python
@patch('src.ai_summarizer.dashscope')
def test_qwen_provider_success(mock_dashscope):
    """测试成功调用通义千问API"""
    from src.ai_summarizer import QwenProvider
    
    # Mock成功响应
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.output.text = "这是一个Python Web框架，提供高性能异步处理能力。"
    mock_dashscope.Generation.call.return_value = mock_response
    
    provider = QwenProvider()
    repo = {
        'name': 'fastapi/fastapi',
        'description': 'FastAPI framework',
        'language': 'Python',
        'stars_today': '123'
    }
    
    summary = provider.generate_summary(repo)
    
    assert summary == "这是一个Python Web框架，提供高性能异步处理能力。"
    assert mock_dashscope.Generation.call.called


@patch('src.ai_summarizer.dashscope')
@patch('src.ai_summarizer.time.sleep')
def test_qwen_provider_retry_on_failure(mock_sleep, mock_dashscope):
    """测试API失败时的重试机制"""
    from src.ai_summarizer import QwenProvider
    
    # 第1次失败，第2次成功
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.output.text = "成功的总结"
    
    mock_dashscope.Generation.call.side_effect = [
        Exception("Network error"),
        mock_response
    ]
    
    provider = QwenProvider()
    repo = {'name': 'test', 'description': 'test', 'language': 'Python', 'stars_today': '10'}
    
    summary = provider.generate_summary(repo)
    
    assert summary == "成功的总结"
    assert mock_dashscope.Generation.call.call_count == 2
    assert mock_sleep.call_count == 1  # 第1次失败后sleep


@patch('src.ai_summarizer.dashscope')
@patch('src.ai_summarizer.time.sleep')
def test_qwen_provider_all_retries_fail(mock_sleep, mock_dashscope):
    """测试所有重试都失败后返回None"""
    from src.ai_summarizer import QwenProvider
    
    mock_dashscope.Generation.call.side_effect = Exception("API Error")
    
    provider = QwenProvider()
    repo = {'name': 'test', 'description': 'test', 'language': 'Python', 'stars_today': '10'}
    
    summary = provider.generate_summary(repo)
    
    assert summary is None
    assert mock_dashscope.Generation.call.call_count == 3
    assert mock_sleep.call_count == 2  # 前2次失败后sleep
```

### Step 2: 运行测试验证失败

运行：`python -m pytest tests/test_ai_summarizer.py::test_qwen_provider_success -v`

预期：FAIL - dashscope模块不存在或逻辑未实现

### Step 3: 安装dashscope依赖

在 `requirements.txt` 末尾添加：

```
dashscope>=1.14.0
```

运行：`pip install dashscope`

### Step 4: 实现API调用逻辑

在 `src/ai_summarizer.py` 中，修改 `QwenProvider.generate_summary()` 方法：

```python
    def generate_summary(self, repo: Dict) -> Optional[str]:
        """生成项目总结，带重试机制
        
        Args:
            repo: 项目信息字典
            
        Returns:
            str: AI生成的总结，失败返回None
        """
        import dashscope
        
        prompt = self._build_prompt(repo)
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"正在为项目 {repo['name']} 生成AI总结 (尝试 {attempt + 1}/{self.max_retries})")
                
                response = dashscope.Generation.call(
                    model=self.model,
                    prompt=prompt,
                    api_key=self.api_key
                )
                
                if response.status_code == 200:
                    summary = response.output.text
                    logger.info(f"成功生成总结: {summary[:50]}...")
                    return summary
                else:
                    logger.warning(f"API返回非200状态码: {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"API调用失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    sleep_time = 2 ** attempt  # 指数退避
                    logger.info(f"等待 {sleep_time} 秒后重试...")
                    time.sleep(sleep_time)
        
        logger.error(f"项目 {repo['name']} 的AI总结生成失败，已用尽所有重试")
        return None
    
    def _build_prompt(self, repo: Dict) -> str:
        """构建Prompt模板
        
        Args:
            repo: 项目信息
            
        Returns:
            str: 完整的prompt
        """
        return f"""你是一个GitHub项目分析专家。请为以下项目生成简洁的中文总结（150-200字）：

项目名称：{repo['name']}
描述：{repo.get('description', '无描述')}
编程语言：{repo.get('language', '未知')}
今日新增stars：{repo.get('stars_today', '0')}

请包含：
1. 项目用途和核心功能
2. 主要特点和优势
3. 适用场景
4. 技术亮点（如果明显）

用通俗易懂的语言，避免过于技术化的术语。"""
```

### Step 5: 运行测试验证通过

运行：`python -m pytest tests/test_ai_summarizer.py -v`

预期：所有测试通过

### Step 6: 提交

```bash
git add src/ai_summarizer.py tests/test_ai_summarizer.py requirements.txt
git commit -m "feat: 实现通义千问API调用和重试机制"
```

---

## Task 4: 批量总结函数

**Files:**
- Modify: `src/ai_summarizer.py`
- Modify: `tests/test_ai_summarizer.py`

### Step 1: 写批量总结测试

在 `tests/test_ai_summarizer.py` 添加：

```python
@patch('src.ai_summarizer.QwenProvider')
def test_summarize_repos_only_first_n(mock_provider_class):
    """测试只总结前5个项目"""
    from src.ai_summarizer import summarize_repos
    
    # Mock provider实例
    mock_provider = Mock()
    mock_provider.generate_summary.return_value = "AI总结内容"
    mock_provider_class.return_value = mock_provider
    
    # 创建10个项目
    repos = [
        {'name': f'repo{i}', 'description': 'test', 'language': 'Python', 'stars_today': '10'}
        for i in range(10)
    ]
    
    result = summarize_repos(repos)
    
    # 应该调用5次
    assert mock_provider.generate_summary.call_count == 5
    
    # 前5个有ai_summary
    for i in range(5):
        assert result[i]['ai_summary'] == "AI总结内容"
    
    # 后5个没有ai_summary
    for i in range(5, 10):
        assert 'ai_summary' not in result[i]


@patch('src.ai_summarizer.QwenProvider')
def test_summarize_repos_handles_partial_failure(mock_provider_class):
    """测试部分项目总结失败的情况"""
    from src.ai_summarizer import summarize_repos
    
    mock_provider = Mock()
    # 第1个成功，第2个失败，第3个成功
    mock_provider.generate_summary.side_effect = [
        "总结1",
        None,  # 失败
        "总结3",
        "总结4",
        "总结5"
    ]
    mock_provider_class.return_value = mock_provider
    
    repos = [{'name': f'repo{i}'} for i in range(5)]
    
    result = summarize_repos(repos)
    
    assert result[0]['ai_summary'] == "总结1"
    assert result[1]['ai_summary'] is None
    assert result[2]['ai_summary'] == "总结3"


def test_summarize_repos_when_disabled(monkeypatch):
    """测试禁用AI总结时直接返回"""
    from src.ai_summarizer import summarize_repos
    
    monkeypatch.setenv('ENABLE_AI_SUMMARY', 'false')
    
    repos = [{'name': 'test'}]
    result = summarize_repos(repos)
    
    # 不应添加ai_summary字段
    assert 'ai_summary' not in result[0]
```

### Step 2: 运行测试验证失败

运行：`python -m pytest tests/test_ai_summarizer.py::test_summarize_repos_only_first_n -v`

预期：FAIL - summarize_repos函数不存在

### Step 3: 实现批量总结函数

在 `src/ai_summarizer.py` 末尾添加：

```python
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
```

### Step 4: 运行测试验证通过

运行：`python -m pytest tests/test_ai_summarizer.py -v`

预期：所有测试通过

### Step 5: 提交

```bash
git add src/ai_summarizer.py tests/test_ai_summarizer.py
git commit -m "feat: 实现批量AI总结功能"
```

---

## Task 5: 主流程集成

**Files:**
- Modify: `src/main.py`
- Test: 手动测试

### Step 1: 修改main.py集成AI总结

在 `src/main.py` 中，找到获取trending数据后的位置，添加AI总结调用：

```python
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
```

### Step 2: 验证导入无错误

运行：`python -c "from src.main import main; print('Import OK')"`

预期：输出 "Import OK"

### Step 3: 提交

```bash
git add src/main.py
git commit -m "feat: 在主流程中集成AI总结功能"
```

---

## Task 6: 邮件模板更新

**Files:**
- Modify: `templates/email_template.html`
- Test: `tests/test_email_sender.py`

### Step 1: 写模板渲染测试

在 `tests/test_email_sender.py` 添加：

```python
def test_render_email_with_ai_summary():
    """测试渲染包含AI总结的邮件"""
    from src.email_sender import render_email_content
    
    repos = [
        {
            'name': 'test/repo',
            'description': 'Original description',
            'url': 'https://github.com/test/repo',
            'language': 'Python',
            'stars': '1000',
            'stars_today': '100',
            'ai_summary': '这是一个优秀的Python项目，提供高性能的数据处理能力。适用于大规模数据分析场景。'
        }
    ]
    
    html = render_email_content(repos)
    
    # 检查AI总结区块存在
    assert '🤖 AI深度解析' in html
    assert '这是一个优秀的Python项目' in html
    assert 'ai-summary' in html


def test_render_email_without_ai_summary():
    """测试没有AI总结时的渲染"""
    from src.email_sender import render_email_content
    
    repos = [
        {
            'name': 'test/repo',
            'description': 'Description',
            'url': 'https://github.com/test/repo',
            'language': 'Python',
            'stars': '1000',
            'stars_today': '100'
            # 没有 ai_summary 字段
        }
    ]
    
    html = render_email_content(repos)
    
    # 不应包含AI总结区块
    assert '🤖 AI深度解析' not in html
    assert 'ai-summary' not in html
```

### Step 2: 运行测试验证失败

运行：`python -m pytest tests/test_email_sender.py::test_render_email_with_ai_summary -v`

预期：FAIL - 模板中没有AI总结区块

### Step 3: 修改HTML模板

在 `templates/email_template.html` 中，找到项目描述部分（`.description`），在其后添加AI总结区块：

```html
          <p class="description">{{ repo.description or '暂无描述' }}</p>
          
          <!-- AI总结区块 -->
          {% if repo.ai_summary %}
          <div class="ai-summary">
            <div class="ai-badge">🤖 AI深度解析</div>
            <p>{{ repo.ai_summary }}</p>
          </div>
          {% endif %}
          
          <div class="repo-meta">
```

在 `<style>` 标签内添加CSS样式（在 `.repo-meta` 样式后）：

```css
      .ai-summary {
        background-color: #f0f8ff;
        border: 1px dashed #4a9eff;
        border-radius: 8px;
        padding: 12px;
        margin-top: 10px;
      }
      
      .ai-badge {
        display: inline-block;
        background: linear-gradient(135deg, #667eea 0%, #4a9eff 100%);
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        margin-bottom: 8px;
      }
      
      .ai-summary p {
        font-size: 14px;
        line-height: 1.6;
        color: #333;
        margin: 0;
      }
```

### Step 4: 运行测试验证通过

运行：`python -m pytest tests/test_email_sender.py -v`

预期：所有测试通过

### Step 5: 提交

```bash
git add templates/email_template.html tests/test_email_sender.py
git commit -m "feat: 更新邮件模板支持AI总结展示"
```

---

## Task 7: GitHub Actions工作流更新

**Files:**
- Modify: `.github/workflows/daily-trending.yml`

### Step 1: 添加AI总结环境变量

在 `.github/workflows/daily-trending.yml` 的 `env` 部分添加：

```yaml
      - name: 运行trending邮件推送
        env:
          EMAIL_SENDER: ${{ secrets.EMAIL_SENDER }}
          EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
          EMAIL_RECEIVER: ${{ secrets.EMAIL_RECEIVER }}
          TRENDING_LIMIT: 10
          ENABLE_AI_SUMMARY: ${{ secrets.ENABLE_AI_SUMMARY || 'false' }}
          QWEN_API_KEY: ${{ secrets.QWEN_API_KEY || '' }}
          QWEN_MODEL: ${{ secrets.QWEN_MODEL || 'qwen-turbo' }}
        run: |
          python -m src.main
```

### Step 2: 验证YAML语法

运行：`python -c "import yaml; yaml.safe_load(open('.github/workflows/daily-trending.yml'))"`

预期：无错误

### Step 3: 提交

```bash
git add .github/workflows/daily-trending.yml
git commit -m "feat: 更新GitHub Actions支持AI总结配置"
```

---

## Task 8: 文档更新

**Files:**
- Modify: `README.md`

### Step 1: 在README中添加AI总结功能章节

在 `README.md` 的"常见问题"章节前添加：

```markdown
## AI总结功能（可选）

启用AI总结功能可为trending项目生成详细的中文解析，帮助快速了解项目核心价值。

### 功能特性

- ✅ 自动为前5个trending项目生成AI总结
- ✅ 包含项目用途、特点、适用场景、技术亮点
- ✅ 支持启用/禁用，不影响基础功能
- ✅ API失败自动降级，确保邮件正常发送

### 如何启用

**1. 获取通义千问API Key**

访问 [阿里云DashScope](https://dashscope.aliyun.com/)：
1. 注册/登录阿里云账号
2. 开通DashScope服务
3. 创建API Key（首次注册赠送免费额度）

**2. 配置GitHub Secrets**

在仓库的 `Settings` → `Secrets and variables` → `Actions` 中添加：

| Secret名称 | 说明 | 示例 |
|-----------|------|------|
| `ENABLE_AI_SUMMARY` | 是否启用AI总结 | `true` |
| `QWEN_API_KEY` | 通义千问API密钥 | `sk-xxxxx...` |
| `QWEN_MODEL` | 使用的模型（可选） | `qwen-turbo` |

**3. 测试运行**

配置完成后，手动触发一次workflow验证效果。

### 成本说明

- **模型选择**: qwen-turbo（默认，性价比高）
- **日消耗**: 约0.02元/天
- **月成本**: 约0.6元/月
- **年成本**: 约7.2元/年

可随时通过设置 `ENABLE_AI_SUMMARY=false` 关闭功能。

### 效果展示

启用后，邮件中每个trending项目卡片会显示：

```
🤖 AI深度解析
这是一个高性能的Web框架，基于Python异步编程构建。
主要特点包括快速的请求处理、自动API文档生成、类型安全。
适用于构建RESTful API、微服务后端等场景。
技术亮点是基于Starlette和Pydantic的现代化架构设计。
```
```

### Step 2: 提交

```bash
git add README.md
git commit -m "docs: 添加AI总结功能使用文档"
```

---

## Task 9: 运行完整测试套件

**Files:**
- All test files

### Step 1: 运行所有测试

运行：`python -m pytest tests/ -v`

预期：所有测试通过（应该有13+个测试）

### Step 2: 检查测试覆盖率（可选）

运行：`python -m pytest tests/ --cov=src --cov-report=term-missing`

预期：覆盖率 > 80%

### Step 3: 如果有失败，修复后重新测试

修复任何失败的测试，确保全部通过。

---

## Task 10: 本地端到端测试（可选）

**Files:**
- `.env`

### Step 1: 创建测试环境变量

复制 `.env.example` 为 `.env`，填入真实配置：

```bash
cp .env.example .env
# 编辑.env，填入真实的邮箱和API Key
```

### Step 2: 测试禁用AI的情况

确保 `.env` 中 `ENABLE_AI_SUMMARY=false`

运行：`python -m src.main`

预期：成功发送邮件，无AI总结

### Step 3: 测试启用AI的情况（需要真实API Key）

修改 `.env`：
```
ENABLE_AI_SUMMARY=true
QWEN_API_KEY=你的真实API Key
```

运行：`python -m src.main`

预期：成功发送邮件，前5个项目包含AI总结

### Step 4: 清理测试配置

删除或重置 `.env` 文件，避免提交敏感信息。

---

## Task 11: 最终检查与提交

**Files:**
- All files

### Step 1: 检查git状态

运行：`git status`

确认所有修改都已提交。

### Step 2: 查看提交历史

运行：`git log --oneline`

预期：应该有约11个新提交，描述清晰。

### Step 3: 推送到远程

运行：`git push origin feature/ai-summary`

### Step 4: 准备合并

等待所有测试通过后，准备合并到master分支。

---

## 验收标准

完成后应满足：

- [ ] 所有单元测试通过（13+个测试）
- [ ] Config正确读取AI相关环境变量
- [ ] QwenProvider实现重试和降级逻辑
- [ ] summarize_repos只处理前5个项目
- [ ] 邮件模板正确显示AI总结区块
- [ ] AI功能可通过环境变量启用/禁用
- [ ] GitHub Actions工作流包含AI配置
- [ ] README包含完整的使用文档
- [ ] 所有提交消息清晰明确
- [ ] 无敏感信息（API Key）泄露

## 注意事项

1. **不要提交真实API Key**: .env文件已在.gitignore中
2. **Mock所有API调用**: 测试不应消耗真实API配额
3. **保持向后兼容**: 禁用AI时应与原功能完全一致
4. **错误处理**: AI失败不应影响邮件发送
5. **日志清晰**: 每个步骤都有适当的日志输出

## 依赖安装

执行实现前确保安装：
```bash
pip install dashscope>=1.14.0
```
