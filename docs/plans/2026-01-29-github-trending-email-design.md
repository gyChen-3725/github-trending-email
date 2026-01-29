# GitHub每日趋势邮件推送系统 - 设计文档

**创建日期**: 2026-01-29  
**版本**: 1.0

## 需求概述

开发一个自动化系统，每天早上8点（北京时间）自动获取GitHub的每日trending项目（前10个，所有编程语言），并通过邮件发送到指定的163邮箱。

## 技术选型

- **开发语言**: Python
- **部署方式**: GitHub Actions（免费、无需服务器）
- **邮件服务**: 163邮箱SMTP
- **数据来源**: GitHub Trending API（第三方服务）
- **触发时间**: 每天UTC 0:00（北京时间8:00）

## 整体架构

### 系统组件

1. **Python脚本（main.py）**
   - 使用requests库调用trending API获取数据
   - 使用smtplib发送邮件
   - 使用jinja2模板引擎渲染HTML邮件

2. **GitHub Actions工作流（.github/workflows/daily-trending.yml）**
   - 定时触发：每天UTC 0:00（北京时间8:00）
   - 运行环境：Ubuntu最新版
   - 从GitHub Secrets读取邮箱配置

3. **配置文件**
   - requirements.txt：Python依赖
   - email_template.html：邮件HTML模板
   - config.py：配置管理（读取环境变量）

### 数据流程

```
GitHub Actions定时触发 
  → 运行Python脚本 
  → 调用trending API获取前10个项目 
  → 渲染HTML邮件模板 
  → 通过163邮箱SMTP发送
```

## 核心功能设计

### 1. Trending数据获取模块 (trending_fetcher.py)

**功能**: 从trending API获取每日trending项目数据

**接口设计**:
```python
def fetch_trending_repos(limit=10):
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
```

**数据来源**:
- 使用第三方trending API服务
- 备选方案：爬取GitHub trending页面

**错误处理**:
- 重试机制：最多3次，间隔5秒
- 超时设置：30秒
- 异常捕获：网络错误、JSON解析错误

### 2. 邮件发送模块 (email_sender.py)

**功能**: 通过163邮箱SMTP发送HTML格式的邮件

**SMTP配置**:
- 服务器：smtp.163.com
- 端口：465（SSL）
- 认证：邮箱地址 + 授权码

**接口设计**:
```python
def send_email(repos_data, receiver_email):
    """
    发送trending项目邮件
    
    Args:
        repos_data: 项目数据列表
        receiver_email: 接收邮箱地址
    """
```

**邮件格式**:
- 主题：`🌟 GitHub每日趋势 - {日期}`
- 内容类型：HTML
- 字符编码：UTF-8

### 3. 配置管理模块 (config.py)

**环境变量**:
```python
EMAIL_SENDER      # 发送邮箱（163邮箱）
EMAIL_PASSWORD    # SMTP授权码（非登录密码）
EMAIL_RECEIVER    # 接收邮箱（同发送邮箱）
```

**GitHub Secrets配置**:
在仓库Settings → Secrets中添加上述环境变量

## 邮件内容设计

### 邮件结构

**标题**:
```
🌟 GitHub每日趋势 - 2026-01-29
```

**邮件内容**（HTML格式）:

1. **头部区域**
   - 日期：2026年1月29日
   - 说明：GitHub今日trending项目（所有语言）

2. **项目列表**（每个项目一个卡片）
   - 排名编号：#1, #2, ...
   - 项目名称：可点击链接，跳转到GitHub
   - 项目描述：简短描述
   - 编程语言：带语言图标/标签
   - Star信息：
     - 总star数：⭐ 12,345 stars
     - 今日新增：📈 +123 stars today

3. **底部区域**
   - 数据来源说明
   - 生成时间戳

### 样式设计

- 简洁的卡片式布局
- 响应式设计，适配手机和电脑
- 清晰的层次结构
- 使用图标增强视觉效果

## 项目文件结构

```
SoftwareSkillProject-test/
├── .github/
│   └── workflows/
│       └── daily-trending.yml    # GitHub Actions工作流配置
├── src/
│   ├── main.py                   # 主程序入口
│   ├── config.py                 # 配置管理
│   ├── trending_fetcher.py       # trending数据获取
│   └── email_sender.py           # 邮件发送功能
├── templates/
│   └── email_template.html       # 邮件HTML模板
├── docs/
│   └── plans/
│       └── 2026-01-29-github-trending-email-design.md  # 本文档
├── .env.example                  # 环境变量示例文件
├── .gitignore                    # Git忽略配置
├── requirements.txt              # Python依赖
└── README.md                     # 项目说明文档
```

## 错误处理与可靠性

### 1. API调用失败处理

- **重试机制**: 最多重试3次，指数退避（5秒、10秒、20秒）
- **降级方案**: 如果API持续失败，发送错误通知邮件给用户
- **日志记录**: 记录所有API调用和失败原因

### 2. 邮件发送失败处理

- **连接超时**: 30秒超时设置
- **认证失败**: 明确提示检查授权码
- **发送失败**: 记录详细错误信息到GitHub Actions日志

### 3. 数据异常处理

- **空数据检查**: API返回空数据时不发送邮件
- **默认值填充**: 项目信息缺失时使用"未知"等默认值
- **数据验证**: 确保必要字段（name、url）存在

## 部署与测试

### 本地测试

1. **环境准备**
   ```bash
   pip install -r requirements.txt
   cp .env.example .env
   # 编辑.env文件，填入邮箱配置
   ```

2. **运行测试**
   ```bash
   python src/main.py
   ```

### GitHub Actions配置

1. **添加Secrets**
   - Settings → Secrets and variables → Actions
   - 添加：EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER

2. **手动测试**
   - Actions页面 → daily-trending workflow
   - 点击"Run workflow"手动触发

3. **启用定时任务**
   - 确认手动测试成功后，定时任务会自动生效
   - 每天UTC 0:00（北京时间8:00）执行

### 监控与维护

- **执行日志**: GitHub Actions页面查看每次执行日志
- **失败通知**: GitHub会在workflow失败时发送邮件通知
- **定期检查**: 建议每周检查一次执行状态

## 技术依赖

### Python库

```
requests>=2.31.0       # HTTP请求
jinja2>=3.1.0          # 模板引擎
python-dotenv>=1.0.0   # 环境变量管理
```

### GitHub Actions

- Ubuntu latest环境
- Python 3.11+
- Cron定时触发

## 安全考虑

1. **敏感信息保护**
   - 邮箱密码使用GitHub Secrets存储，不提交到代码仓库
   - .env文件添加到.gitignore

2. **SMTP授权码**
   - 使用专用授权码而非邮箱登录密码
   - 定期更换授权码

3. **API访问**
   - 使用HTTPS协议
   - 设置合理的超时时间

## 未来扩展方向

1. **功能增强**
   - 支持按编程语言筛选
   - 支持weekly/monthly trending
   - 添加trending developers

2. **用户体验**
   - 提供Web界面配置
   - 支持多个邮箱订阅
   - 添加邮件摘要模式（只显示标题）

3. **数据持久化**
   - 记录历史trending数据
   - 生成趋势分析报告

## 实现优先级

**P0 (必须)**: 
- 基础trending获取
- 邮件发送功能
- GitHub Actions定时任务

**P1 (重要)**:
- 错误处理和重试
- HTML邮件模板
- 本地测试支持

**P2 (可选)**:
- 详细的日志记录
- 更丰富的邮件样式

---

**设计确认**: ✅ 已通过用户确认  
**下一步**: 创建实现计划并开始开发
