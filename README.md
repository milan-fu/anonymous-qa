# 一个提问箱（测试版）

一个支持匿名提问和匿名留言的轻量级网站，基于 Flask + SQLite。

**线上地址：[https://anonymous-qa.fun](https://anonymous-qa.fun)**

## 功能

- 📬 **匿名提问** — 向管理员提问，回答后可公开展示
- ✍️ **匿名留言** — 管理员发起话题，大家匿名留言
- 🔑 **管理员面板** — 管理提问和留言，支持置顶、标签、关闭等
- 📷 **图片上传** — 回答和留言支持插入图片
- 📱 **飞书通知** — 新提问、新留言实时推送到手机

## 本地运行

```bash
pip install flask requests
python app.py
# 访问 http://127.0.0.1:5001
```

环境变量（可选）：

- `ADMIN_PASSWORD` — 管理员密码
- `FEISHU_APP_SECRET` — 飞书应用密钥，用于消息推送

## 部署参考

- 服务器部署：[【轻松落地】二十分钟，制作并上传免费网站！](https://www.bilibili.com/video/BV1TCMvzJEtp)
- 飞书通知：[larksuite/cli](https://github.com/larksuite/cli)

## 技术栈

Python 3 + Flask / SQLite / HTML + CSS + Vanilla JS / 飞书 Bot API
