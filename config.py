import os

# 管理员密码 — 优先从环境变量读取，否则使用默认值（部署时请务必修改）
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

# 数据库路径
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "questions.db")

# Flask 密钥（用于 session 签名）
SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")

# 频率限制：每个 IP 每分钟最多提问数
RATE_LIMIT_PER_MINUTE = 10

# 问题字数上限
QUESTION_MAX_LENGTH = 200
