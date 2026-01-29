# 部署指南

## 推送到GitHub

### 1. 创建GitHub仓库

1. 登录 [GitHub](https://github.com)
2. 点击右上角 `+` → `New repository`
3. 填写仓库名称：`github-trending-email` （或其他名称）
4. 选择 `Public` 或 `Private`
5. **不要**勾选 "Initialize this repository with a README"
6. 点击 `Create repository`

### 2. 添加远程仓库并推送

在本地仓库目录执行以下命令：

```bash
# 添加远程仓库（替换YOUR_USERNAME为你的GitHub用户名）
git remote add origin https://github.com/YOUR_USERNAME/github-trending-email.git

# 推送所有分支到远程仓库
git push -u origin master
git push origin feature/github-trending-email

# 或者使用SSH（如果已配置SSH密钥）
# git remote add origin git@github.com:YOUR_USERNAME/github-trending-email.git
# git push -u origin master
```

### 3. 配置GitHub Secrets

在GitHub仓库页面：

1. 进入 `Settings` → `Secrets and variables` → `Actions`
2. 点击 `New repository secret`
3. 添加以下三个secrets：

| 名称 | 值 | 说明 |
|------|-----|------|
| `EMAIL_SENDER` | your_email@163.com | 发送邮箱 |
| `EMAIL_PASSWORD` | YOUR_SMTP_AUTH_CODE | 163邮箱SMTP授权码（不是登录密码！） |
| `EMAIL_RECEIVER` | your_email@163.com | 接收邮箱（可以和发送邮箱相同） |

### 4. 获取163邮箱SMTP授权码

1. 登录 [163邮箱](https://mail.163.com)
2. 点击右上角 `设置` → `POP3/SMTP/IMAP`
3. 找到 `SMTP服务` 并开启
4. 点击 `授权码管理` → `新增授权码`
5. 按提示完成验证
6. 复制生成的授权码（16位字符）
7. 将这个授权码填入GitHub Secret的 `EMAIL_PASSWORD`

**重要提示**：授权码不是邮箱登录密码，是专门用于第三方客户端登录的密码！

### 5. 启用GitHub Actions

1. 进入仓库的 `Actions` 标签
2. 如果看到提示，点击 `I understand my workflows, go ahead and enable them`
3. 找到 `GitHub Daily Trending Email` workflow
4. 点击 `Enable workflow`

### 6. 测试运行

1. 在 `Actions` 标签页
2. 选择 `GitHub Daily Trending Email` workflow
3. 点击右侧 `Run workflow` 按钮
4. 选择 `Branch: master`
5. 点击绿色的 `Run workflow` 按钮
6. 等待几分钟，查看运行结果
7. 检查邮箱是否收到邮件

### 7. 定时任务

一切配置正确后，GitHub Actions会自动在每天早上8点（北京时间）执行。

您也可以在 `.github/workflows/daily-trending.yml` 中修改定时时间：

```yaml
schedule:
  - cron: '0 0 * * *'  # UTC 0:00 = 北京时间 8:00
  # 修改为其他时间，例如：
  # - cron: '0 1 * * *'  # UTC 1:00 = 北京时间 9:00
```

## 故障排查

### Actions执行失败

1. 查看 Actions 运行日志，找到具体错误信息
2. 常见问题：
   - Secret配置错误：检查是否正确填写了三个secrets
   - SMTP认证失败：确认使用的是授权码而不是登录密码
   - 网络问题：GitHub Actions可能暂时无法访问某些服务

### 收不到邮件

1. 检查垃圾邮件箱
2. 确认邮箱地址正确
3. 查看Actions日志确认邮件是否发送成功
4. 尝试手动运行一次workflow测试

### 修改trending参数

如需修改获取的trending项目数量，在 `.github/workflows/daily-trending.yml` 中修改：

```yaml
env:
  TRENDING_LIMIT: 10  # 改为其他数字，如 20
```

## 本地测试

如果想在本地测试而不推送到GitHub：

```bash
# 1. 复制环境变量模板
cp .env.example .env

# 2. 编辑.env文件，填入真实的邮箱配置
# EMAIL_SENDER=your_email@163.com
# EMAIL_PASSWORD=your_smtp_auth_code
# EMAIL_RECEIVER=your_email@163.com

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行程序
python src/main.py

# 5. 检查邮箱
```

## 项目结构说明

```
.
├── .github/workflows/
│   └── daily-trending.yml      # GitHub Actions配置
├── docs/plans/                 # 设计和实现文档
├── src/
│   ├── config.py              # 配置管理
│   ├── trending_fetcher.py    # 数据获取
│   ├── email_sender.py        # 邮件发送
│   └── main.py                # 主程序
├── templates/
│   └── email_template.html    # 邮件模板
├── tests/                     # 测试文件
├── .env.example               # 环境变量示例
├── .gitignore                 # Git忽略配置
├── README.md                  # 项目说明
└── requirements.txt           # Python依赖
```

## 维护建议

1. **定期检查**：每周查看一次Actions执行情况
2. **更新依赖**：每月检查Python依赖是否有安全更新
3. **监控日志**：如果某天没收到邮件，检查Actions日志
4. **备份配置**：记录好SMTP授权码，避免遗忘

---

**祝您使用愉快！** 🎉

如有问题，欢迎提交Issue！
