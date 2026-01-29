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
# 编辑.env文件,填入你的163邮箱配置
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
