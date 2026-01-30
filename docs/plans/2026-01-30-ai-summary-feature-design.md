# GitHub Trending AI总结功能设计文档

**创建日期**: 2026-01-30  
**功能**: 为GitHub trending项目添加AI总结功能  
**状态**: 设计完成，待实现

## 需求概述

在现有的GitHub每日趋势邮件推送系统基础上，增加AI总结功能：
- 使用通义千问API对前5个trending项目生成详细总结
- 总结内容包含：项目用途、核心特点、适用场景、技术亮点
- 作为可选功能，通过环境变量控制启用/禁用
- 确保AI调用失败时不影响基础邮件发送功能

## 技术选型

- **大模型**: 阿里云通义千问 (Qwen API)
- **SDK**: dashscope Python包
- **模型**: qwen-turbo (默认) / qwen-plus (可配置)
- **总结范围**: 前5个trending项目
- **总结长度**: 150-200字/项目

## 系统架构

### 核心组件

#### 1. ai_summarizer.py - AI总结模块

**BaseLLMProvider 抽象基类**
```python
from abc import ABC, abstractmethod
from typing import Dict, Optional

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_summary(self, repo: Dict) -> Optional[str]:
        """生成单个项目的总结"""
        pass
```

**QwenProvider 实现类**
- 通义千问API调用封装
- 重试机制：最多3次，指数退避（2s, 4s, 8s）
- 超时控制：30秒/次
- 错误处理：API失败返回None，调用方降级

**summarize_repos() 主函数**
```python
def summarize_repos(repos: List[Dict]) -> List[Dict]:
    """
    为trending项目批量生成AI总结
    
    Args:
        repos: trending项目列表
        
    Returns:
        增强后的项目列表，每个项目新增 'ai_summary' 字段（可能为None）
    """
```

#### 2. config.py 扩展

新增配置项：
```python
# AI总结功能配置
ENABLE_AI_SUMMARY = os.getenv('ENABLE_AI_SUMMARY', 'false').lower() == 'true'
QWEN_API_KEY = os.getenv('QWEN_API_KEY', '')
QWEN_MODEL = os.getenv('QWEN_MODEL', 'qwen-turbo')
AI_SUMMARY_COUNT = int(os.getenv('AI_SUMMARY_COUNT', '5'))
AI_MAX_RETRIES = int(os.getenv('AI_MAX_RETRIES', '3'))
AI_TIMEOUT = int(os.getenv('AI_TIMEOUT', '30'))
```

配置验证扩展：
- 当 `ENABLE_AI_SUMMARY=true` 时，验证 `QWEN_API_KEY` 不为空

#### 3. main.py 修改

流程调整：
```python
def main():
    # ... 获取trending数据 ...
    repos = fetch_trending_repos(limit=Config.TRENDING_LIMIT)
    
    # AI总结增强（可选）
    if Config.ENABLE_AI_SUMMARY:
        logger.info("AI总结功能已启用，开始生成项目总结...")
        repos = summarize_repos(repos)
    
    # 发送邮件
    send_email(repos)
```

#### 4. 数据结构变更

trending项目字典新增字段：
```python
{
    "name": str,
    "description": str,
    "url": str,
    "language": str,
    "stars": str,
    "stars_today": str,
    "ai_summary": Optional[str]  # 新增字段
}
```

## API调用设计

### Prompt模板

```
你是一个GitHub项目分析专家。请为以下项目生成简洁的中文总结（150-200字）：

项目名称：{name}
描述：{description}
编程语言：{language}
今日新增stars：{stars_today}

请包含：
1. 项目用途和核心功能
2. 主要特点和优势
3. 适用场景
4. 技术亮点（如果明显）

用通俗易懂的语言，避免过于技术化的术语。
```

### 重试与降级策略

**重试机制**
```python
for attempt in range(Config.AI_MAX_RETRIES):
    try:
        response = dashscope.Generation.call(
            model=Config.QWEN_MODEL,
            prompt=prompt,
            api_key=Config.QWEN_API_KEY
        )
        if response.status_code == 200:
            return response.output.text
    except Exception as e:
        logger.warning(f"AI总结失败 (尝试 {attempt+1}/{Config.AI_MAX_RETRIES}): {e}")
        if attempt < Config.AI_MAX_RETRIES - 1:
            time.sleep(2 ** attempt)  # 指数退避
return None  # 全部失败返回None
```

**降级策略**
- 单个项目失败：该项目 `ai_summary=None`，继续处理下一个
- API Key无效：记录错误，所有项目 `ai_summary=None`
- 配额超限：记录警告，停止后续调用，已成功的保留
- 网络超时：重试，全部失败后降级

### 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| API Key无效 | 记录ERROR日志，返回None，不影响邮件发送 |
| 配额超限 | 记录WARNING，停止后续总结，保留已成功的 |
| 网络超时 | 重试3次，失败后返回None |
| 返回内容为空 | 记录WARNING，返回None |
| 其他异常 | 记录ERROR，返回None |

## 邮件模板设计

### HTML结构修改

在项目卡片中添加AI总结区块：

```html
<div class="repo-card">
  <div class="repo-rank">#{loop.index}</div>
  <h3><a href="{{ repo.url }}">{{ repo.name }}</a></h3>
  <p class="description">{{ repo.description or '暂无描述' }}</p>
  
  <!-- AI总结区块 (新增) -->
  {% if repo.ai_summary %}
  <div class="ai-summary">
    <div class="ai-badge">🤖 AI深度解析</div>
    <p>{{ repo.ai_summary }}</p>
  </div>
  {% endif %}
  
  <div class="repo-meta">
    <!-- language, stars, stars_today -->
  </div>
</div>
```

### CSS样式

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

### 视觉效果

- **AI总结区块**：浅蓝色背景，与原description区分
- **徽章**：渐变蓝色，机器人emoji，增加科技感
- **字体**：比description稍小，视觉层次清晰
- **间距**：与上方description保持10px间距

## 测试策略

### 单元测试 (test_ai_summarizer.py)

```python
# 1. 测试成功调用
def test_qwen_provider_success(mock_dashscope):
    mock_dashscope.Generation.call.return_value = MockResponse(
        status_code=200,
        output=MockOutput(text="这是AI生成的总结...")
    )
    provider = QwenProvider()
    summary = provider.generate_summary(sample_repo)
    assert summary == "这是AI生成的总结..."

# 2. 测试重试机制
def test_qwen_provider_retry(mock_dashscope):
    # 第1次失败，第2次成功
    mock_dashscope.Generation.call.side_effect = [
        Exception("Network error"),
        MockResponse(status_code=200, output=MockOutput(text="成功"))
    ]
    provider = QwenProvider()
    summary = provider.generate_summary(sample_repo)
    assert summary == "成功"
    assert mock_dashscope.Generation.call.call_count == 2

# 3. 测试降级
def test_qwen_provider_fallback(mock_dashscope):
    mock_dashscope.Generation.call.side_effect = Exception("API Error")
    provider = QwenProvider()
    summary = provider.generate_summary(sample_repo)
    assert summary is None

# 4. 测试只总结前5个
def test_summarize_repos_count(mock_provider):
    repos = [{"name": f"repo{i}"} for i in range(10)]
    result = summarize_repos(repos)
    # 只有前5个有ai_summary
    assert result[0]['ai_summary'] is not None
    assert result[4]['ai_summary'] is not None
    assert 'ai_summary' not in result[5] or result[5]['ai_summary'] is None

# 5. 测试禁用状态
def test_summarize_disabled(monkeypatch):
    monkeypatch.setenv('ENABLE_AI_SUMMARY', 'false')
    repos = [{"name": "test"}]
    # main.py 中不应调用 summarize_repos
```

### 集成测试

```python
def test_full_flow_with_ai_summary(mock_dashscope, mock_smtp):
    # 1. Mock trending数据
    # 2. Mock AI总结API
    # 3. 执行main()
    # 4. 验证邮件HTML包含ai-summary区块
    # 5. 验证前5个项目有总结，后5个没有
```

### Mock策略

- **dashscope API**: 使用 `unittest.mock.patch` Mock所有API调用
- **避免真实调用**: 测试不消耗API配额
- **边界测试**: 空响应、超时、异常等场景

## 配置管理

### .env.example 更新

```bash
# === 邮件配置 ===
EMAIL_SENDER=your_email@163.com
EMAIL_PASSWORD=your_smtp_authorization_code
EMAIL_RECEIVER=your_email@163.com

# === Trending配置 ===
TRENDING_LIMIT=10

# === AI总结配置 (可选) ===
ENABLE_AI_SUMMARY=false
QWEN_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
QWEN_MODEL=qwen-turbo
AI_SUMMARY_COUNT=5
AI_MAX_RETRIES=3
AI_TIMEOUT=30
```

### GitHub Secrets 配置

如果启用AI总结，需在GitHub仓库 Settings → Secrets 中添加：
- `QWEN_API_KEY`: 通义千问API密钥

### GitHub Actions 工作流更新

`.github/workflows/daily-trending.yml`:
```yaml
- name: 运行trending邮件推送
  env:
    EMAIL_SENDER: ${{ secrets.EMAIL_SENDER }}
    EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
    EMAIL_RECEIVER: ${{ secrets.EMAIL_RECEIVER }}
    TRENDING_LIMIT: 10
    ENABLE_AI_SUMMARY: ${{ secrets.ENABLE_AI_SUMMARY || 'false' }}
    QWEN_API_KEY: ${{ secrets.QWEN_API_KEY }}
  run: python -m src.main
```

## 依赖管理

### requirements.txt 新增

```
dashscope>=1.14.0
```

### 兼容性

- Python 3.11+
- 与现有依赖无冲突

## 成本估算

### API价格（通义千问）

- **qwen-turbo**: 约 0.008元/千tokens
- **qwen-plus**: 约 0.04元/千tokens

### 使用估算

**每日消耗**:
- 5个项目
- 每个项目：约300 tokens输入 + 200 tokens输出 = 500 tokens
- 总计：2500 tokens/天

**费用计算**:
- qwen-turbo: 2500 tokens × 0.008元/千tokens = **0.02元/天**
- 月成本: 0.02 × 30 = **0.6元/月**
- 年成本: 0.6 × 12 = **7.2元/年**

### 成本优化

1. 使用 qwen-turbo 而非 qwen-plus（节省80%）
2. 只总结前5个项目（而非全部10个）
3. 失败重试不超过3次
4. 可通过 `ENABLE_AI_SUMMARY=false` 完全关闭

## 文档更新计划

### README.md 新增章节

**AI总结功能（可选）**

启用AI总结功能可为trending项目生成详细解析：

1. **获取通义千问API Key**
   - 访问 [阿里云DashScope](https://dashscope.aliyun.com/)
   - 注册并创建API Key
   - 首次注册赠送免费额度

2. **配置GitHub Secrets**
   ```
   ENABLE_AI_SUMMARY=true
   QWEN_API_KEY=sk-your-api-key
   ```

3. **成本说明**
   - 约 0.02元/天，0.6元/月
   - 可随时关闭（设置 ENABLE_AI_SUMMARY=false）

4. **效果展示**
   - 邮件中每个项目卡片会显示"🤖 AI深度解析"区块
   - 包含项目用途、特点、适用场景、技术亮点

### DEPLOY.md 更新

在部署指南中添加AI总结功能的配置步骤。

## 实现顺序

1. **Phase 1: 核心功能**
   - 创建 `src/ai_summarizer.py`
   - 实现 BaseLLMProvider 和 QwenProvider
   - 实现 summarize_repos() 函数

2. **Phase 2: 配置集成**
   - 扩展 `src/config.py`
   - 修改 `src/main.py`
   - 更新 `.env.example`

3. **Phase 3: 模板更新**
   - 修改 `templates/email_template.html`
   - 添加AI总结区块和样式

4. **Phase 4: 测试**
   - 编写 `tests/test_ai_summarizer.py`
   - 更新现有测试（适配新数据结构）
   - 运行完整测试套件

5. **Phase 5: 文档与部署**
   - 更新 README.md
   - 更新 DEPLOY.md
   - 更新 GitHub Actions 工作流
   - 更新 requirements.txt

## 风险与应对

### 风险1: API调用失败率高

**应对**:
- 重试机制（3次）
- 降级到原始description
- 不影响邮件发送

### 风险2: API成本超预期

**应对**:
- 只总结前5个项目
- 使用性价比高的 qwen-turbo
- 可随时通过环境变量关闭

### 风险3: 总结质量不佳

**应对**:
- 精心设计Prompt模板
- 提供示例输出格式
- 可后续调整Prompt或切换模型

### 风险4: 依赖包兼容性

**应对**:
- 使用稳定版本 dashscope>=1.14.0
- 本地测试验证
- CI/CD自动测试

## 未来扩展

1. **支持更多LLM**
   - 添加 OpenAI、Claude Provider
   - 通过 `LLM_PROVIDER` 环境变量切换

2. **缓存机制**
   - 避免重复总结同一项目
   - Redis或本地文件缓存

3. **多语言支持**
   - 根据项目语言生成对应语言的总结
   - 中英文自动切换

4. **自定义Prompt**
   - 允许用户自定义总结风格
   - 支持模板变量

## 验收标准

- [ ] 所有单元测试通过
- [ ] 集成测试验证完整流程
- [ ] 本地测试成功发送带AI总结的邮件
- [ ] GitHub Actions成功运行
- [ ] 文档完整更新
- [ ] 禁用AI功能时不影响原有功能
- [ ] API失败时邮件正常发送（降级）
- [ ] 代码通过code review

## 总结

本设计采用直接集成方案，在现有系统基础上添加AI总结功能作为可选增强。通过抽象接口设计支持未来扩展，通过完善的错误处理和降级机制确保系统稳定性。成本可控（约0.6元/月），功能可随时启用/禁用，符合YAGNI原则。
