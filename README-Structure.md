# 匿名提问箱 — 项目总结

## 一、项目概述

匿名提问箱，已部署上线。

- **线上地址**：`https://anonymous-qa.fun`（Cloudflare Tunnel + HTTPS）
- **首页**（`/`）：双入口卡片（📬 匿名提问 / ✍️ 匿名留言）
- **匿名提问**（`/ask`）：匿名提问，浏览已公开展示的问答及追答链，点击弹窗查看详情
- **匿名留言**（`/answer`）：管理员发起的提问，所有人匿名留言，公开可见
- **我的问题**（`/my`）：Cookie + 私密密钥双重追踪，追问，点击弹窗查看详情
- **管理员面板**（`/admin`）：管理提问箱 + 管理留言箱两个 tab，支持置顶、帮助标识、草稿、关闭留言等
- **私密链接**（`/q/<id>?key=`）：不依赖 Cookie 查看问题

**线上地址**：`http://120.55.13.203`

---

## 二、技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3 + Flask |
| 数据库 | SQLite（`data/questions.db`） |
| 前端 | HTML + CSS + Vanilla JS（Jinja2 模板） |
| 消息推送 | 飞书 Bot API（异步通知） |
| 部署 | 阿里云轻量服务器 + 宝塔面板 + Nginx 反向代理 |

---

## 三、数据模型

### questions 表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | TEXT (UUID) | 主键 |
| `content` | TEXT | 内容，上限 200 字 |
| `asker_cookie_id` | TEXT | 匿名 Cookie ID |
| `asker_ip` | TEXT | IP 地址 |
| `is_answered` | INTEGER | 是否已回答 |
| `answer_content` | TEXT | 回答内容 |
| `is_visible` | INTEGER | 是否公开展示 |
| `created_at` | TEXT | 创建时间 (ISO 8601 UTC) |
| `answered_at` | TEXT | 首次回答时间 |
| `modified_at` | TEXT | 最后修改时间 |
| `secret_key` | TEXT | 私密密钥 (token_urlsafe 16) |
| `parent_id` | TEXT | 父问题 ID（追问/留言） |
| `is_admin_post` | INTEGER | 管理员发起提问 |
| `is_pinned` | INTEGER | 是否置顶 |
| `pinned_at` | TEXT | 置顶时间（用于排序） |
| `is_help` | INTEGER | 帮助文档标识（排最前） |
| `is_closed` | INTEGER | 关闭留言 |
| `is_admin_answer` | INTEGER | 管理员留言标记（粉色背景） |
| `tag` | TEXT | 自定义标签（限 10 字） |
| `nickname` | TEXT | 用户昵称（选填） |
| `draft_content` | TEXT | 管理员回答草稿 |

### ip_cache 表

| 字段 | 说明 |
|------|------|
| `ip` | IP 地址 |
| `location` | 归属地 |
| `updated_at` | 更新时间 |

---

## 四、文件结构

```
html/
├── app.py                 # Flask 路由 + API + Jinja2 filter (bjt)
├── config.py              # 配置
├── database.py            # 数据库初始化 + 迁移 + CRUD
├── notify.py              # 飞书消息推送（异步）
├── requirements.txt       # flask, requests
├── static/
│   ├── style.css
│   └── script.js          # 提问页 JS（ask 页引用）
├── templates/
│   ├── base.html
│   ├── index.html         # 首页（双入口）
│   ├── ask.html           # 匿名提问页
│   ├── answer.html        # 匿名留言页（内联 JS）
│   ├── my.html            # 我的问题
│   ├── admin.html         # 管理员面板（内联 JS）
│   ├── admin_login.html
│   ├── question_detail.html
│   └── question_not_found.html
└── data/
    └── questions.db       # SQLite 数据库（不提交 git）
```

---

## 五、API 接口

### 公开

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/questions/visible` | 公开问答列表 |
| POST | `/api/questions` | 提交问题或追问 |
| GET | `/api/questions/<id>/follow-ups` | 追问列表 |
| GET | `/api/questions/stats` | 可见问题数 |
| GET | `/api/posts` | 管理员提问列表 |
| GET | `/api/posts/<id>` | 单个提问 + 回答 |
| POST | `/api/posts/<id>/answers` | 提交匿名留言 |
| GET | `/api/posts/stats` | 提问数量 |

### 匿名用户

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/my-questions` | 我的问题 |

### 管理员（需登录）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/admin/login` | 登录 |
| POST | `/api/admin/logout` | 退出 |
| GET | `/api/admin/stats` | 统计（全部/未答/已答/公开） |
| GET | `/api/admin/questions` | 问题列表（`?filter=`） |
| PUT | `/api/admin/questions/<id>` | 更新回答/展示 |
| DELETE | `/api/admin/questions/<id>` | 删除问题 |
| POST | `/api/admin/questions/<id>/pin` | 切换置顶 |
| PUT | `/api/admin/pins/reorder` | 重排置顶 |
| POST | `/api/admin/questions/<id>/help` | 切换帮助标识 |
| PUT | `/api/admin/questions/<id>/tag` | 设置自定义 tag |
| PUT | `/api/admin/questions/<id>/draft` | 保存草稿 |
| GET | `/api/admin/posts` | 管理员提问列表 |
| POST | `/api/admin/posts` | 创建提问 |
| DELETE | `/api/admin/posts/<id>` | 删除提问 |
| POST | `/api/admin/posts/<id>/close` | 切换关闭留言 |
| POST | `/api/admin/posts/<id>/admin-answer` | 管理员留言 |
| PUT | `/api/admin/answers/<id>/visibility` | 切换回答可见性 |
| PUT | `/api/admin/posts/<id>/answers/reorder` | 重排回答置顶 |

---

## 六、飞书通知

- 新提问 → `📬 有新提问`
- 新追问 → `🔔 有新追问`
- 新留言 → `💬「帖子标题」有新留言`

配置：环境变量 `FEISHU_APP_SECRET`，异步发送，失败不影响主流程。

---

## 七、部署

| 项 | 值 |
|-----|-----|
| 服务器 | 阿里云 `120.55.13.203` |
| 面板 | 宝塔 + Nginx |
| 项目路径 | `/www/wwwroot/anonymous-qa/` |
| 启动 | `./84be5662b8f470bfdf0922858731c342_venv/bin/python3 -u app.py` |
| 日志 | `/var/log/qa_app.log` |
| SSH | 密钥免密登录 |
| 环境变量 | 在启动前 `export FEISHU_APP_SECRET=xxx` |
