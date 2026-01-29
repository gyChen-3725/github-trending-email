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

