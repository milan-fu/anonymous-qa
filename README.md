# 一个提问箱（测试版）

一个支持匿名提问和匿名留言的轻量级网站，基于 Flask + SQLite。

## 功能

- 📬 **匿名提问** — 向管理员提问，回答后可公开展示
- ✍️ **匿名留言** — 管理员发起话题，大家匿名留言
- 🔑 **管理员面板** — 管理提问和留言，支持置顶、标签、关闭等
- 📷 **图片上传** — 回答和留言支持插入图片
- 📱 **飞书通知** — 新提问、新留言实时推送到手机

## 快速开始

```bash
# 1. 安装依赖
pip install flask requests

# 2. 配置环境变量（可选）
export ADMIN_PASSWORD="你的管理密码"
export FEISHU_APP_SECRET="你的飞书应用密钥"  # 用于消息推送

# 3. 启动
python app.py

# 4. 访问 http://127.0.0.1:5001
```

## 部署到服务器

参考视频教程：[阿里云服务器 + 宝塔面板部署指南](https://www.bilibili.com/video/BV1TCMvzJEtp)

简要步骤：
1. 购买阿里云轻量服务器，安装宝塔面板
2. 宝塔面板中创建 Python 项目，指向项目目录
3. 安装依赖，启动 Flask 应用
4. 配置 Nginx 反向代理
5. （可选）购买域名并解析到服务器 IP

## 飞书通知配置

1. 在[飞书开放平台](https://open.feishu.cn)创建企业自建应用
2. 获取 App ID 和 App Secret
3. 在服务器上设置环境变量 `FEISHU_APP_SECRET`
4. 应用需要开启 `im:message` 权限

飞书 CLI 工具参考：[larksuite/cli](https://github.com/larksuite/cli)

## 技术栈

- Python 3 + Flask
- SQLite
- HTML + CSS + Vanilla JS
- 飞书 Bot API

## 项目结构

```
├── app.py          # Flask 路由和 API
├── config.py       # 配置文件
├── database.py     # 数据库操作
├── notify.py       # 飞书消息推送
├── static/         # CSS 和 JS
└── templates/      # 页面模板
```
