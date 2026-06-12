# 匿名问答网站 — 项目总结

## 一、项目概述

匿名问答网站（Anonymous Q&A Box），已部署上线。

- **提问 & 浏览页**（`/`）：匿名提问，浏览已公开展示的问答及追答链，点击条目弹窗查看详情
- **我的问题页**（`/my`）：Cookie + 私密密钥双重追踪，追问，点击条目弹窗查看详情
- **管理员面板**（`/admin`）：密码登录，筛选问题，弹窗内回答/编辑/展示控制，未回答计数

**线上地址**：`http://120.55.13.203`

---

## 二、技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3 + Flask |
| 数据库 | SQLite（`data/questions.db`） |
| 前端 | HTML + CSS + Vanilla JS（Jinja2 模板） |
| 部署 | 阿里云轻量服务器 + 宝塔面板 + Nginx 反向代理 |
| 版本控制 | Git（本地仓库） |

---

## 三、数据模型

### questions 表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | TEXT (UUID) | 主键 |
| `content` | TEXT | 问题内容，上限 200 字 |
| `asker_cookie_id` | TEXT | 匿名 Cookie ID |
| `asker_ip` | TEXT | 提问者 IP（仅管理员可见） |
| `is_answered` | BOOLEAN | 是否已回答 |
| `answer_content` | TEXT | 回答内容 |
| `is_visible` | BOOLEAN | 是否公开 |
| `created_at` | DATETIME | 提问时间 |
| `answered_at` | DATETIME | 首次回答时间 |
| `secret_key` | TEXT | 私密密钥 |
| `parent_id` | TEXT | 追问所属的父问题 ID |
| `modified_at` | DATETIME | 最后修改时间 |

### ip_cache 表

| 字段 | 说明 |
|------|------|
| `ip` | IP 地址 |
| `location` | 归属地（如 "中国 北京市 北京"） |

---

## 四、核心机制

### 匿名追踪
1. 首次访问生成 UUID → Cookie（httpOnly, 10 年），所有提问绑定该 Cookie
2. 每个问题生成 `secret_key` → 私密链接 `/q/<id>?key=<secret>`，不依赖 Cookie 也能追踪
3. 打开私密链接自动认领到当前浏览器 Cookie → 出现在「我的问题」中
4. 换浏览器/清 Cookie → 丢失 Cookie 关联，但私密链接仍可用

### 追问追答
- 仅已回答的问题可追问（API 校验 + 前端隐藏追问框）
- 有未回答追问时隐藏追问输入框
- 公开页仅展示已回答的追问，未回答追问只在「我的问题」和密钥链接中显示

### 时间显示
- 所有时间精确到分钟（北京时间 UTC+8）
- 未修改 → 显示"回答时间"
- 已修改 → 显示"最后修改时间"

### 频率限制
- 每 IP 每分钟 10 次

---

## 五、文件结构

```
html/
├── app.py                     # Flask 路由 + API + Jinja2 filter (bjt)
├── config.py                  # 配置（密码、频率限制、路径等）
├── database.py                # 数据库初始化 + 迁移 + CRUD
├── requirements.txt           # flask
├── 200-ip-polished-lampson.md # 项目文档（本文件）
├── static/
│   ├── style.css              # 全局样式
│   └── script.js              # 前端交互逻辑
└── templates/
    ├── base.html              # 基础模板
    ├── index.html             # 公开提问 & 浏览页
    ├── my.html                # 我的问题页
    ├── admin.html             # 管理员面板
    ├── admin_login.html       # 管理员登录
    ├── question_detail.html   # 私密链接详情页
    └── question_not_found.html # 404 页
```

---

## 六、API 接口

### 公开

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/questions/visible` | 公开问答列表（含已回答追答） |
| POST | `/api/questions` | 提交问题或追问（`content`, `parent_id`） |
| GET | `/api/questions/<id>/follow-ups` | 获取追问列表 |

### 匿名用户

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/my-questions` | 我的问题（含追问） |

### 管理员（需登录）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/admin/login` | 登录 |
| POST | `/api/admin/logout` | 退出 |
| GET | `/api/admin/stats` | 未回答总数 |
| GET | `/api/admin/questions` | 问题列表（`?filter=`） |
| PUT | `/api/admin/questions/<id>` | 更新回答/展示状态 |

---

## 七、部署信息

- 服务器：阿里云轻量 `120.55.13.203`（Ubuntu）
- 面板：宝塔（Python 项目管理器 + Nginx）
- 项目路径：`/www/wwwroot/anonymous-qa/`
- Nginx：静态文件缓存，动态内容不缓存
- SSH：已配置密钥免密登录

---

## 八、已知约定

- Git commit 前需用户批准
- 不随便删除服务器数据
- `btn.closest()` 必须先 `.follow-up-item` 再 `.qa-card`
- UUID 一致性：`get_or_create_asker_id()` 存到 `g._new_asker_id`，`set_asker_cookie()` 读取
