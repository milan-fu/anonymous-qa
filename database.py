import secrets
import sqlite3
import uuid
from datetime import datetime, timezone
from config import DATABASE_PATH


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def migrate_add_column(conn, table, column, col_type):
    """安全的列迁移"""
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
    except sqlite3.OperationalError:
        pass


def init_db():
    """初始化数据库表"""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            asker_cookie_id TEXT NOT NULL,
            asker_ip TEXT NOT NULL,
            is_answered INTEGER NOT NULL DEFAULT 0,
            answer_content TEXT DEFAULT '',
            is_visible INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            answered_at TEXT DEFAULT NULL,
            secret_key TEXT DEFAULT '',
            parent_id TEXT DEFAULT NULL,
            modified_at TEXT DEFAULT NULL
        )
    """)
    # 旧表迁移
    migrate_add_column(conn, "questions", "secret_key", "TEXT DEFAULT ''")
    migrate_add_column(conn, "questions", "parent_id", "TEXT DEFAULT NULL")
    migrate_add_column(conn, "questions", "modified_at", "TEXT DEFAULT NULL")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS ip_cache (
            ip TEXT PRIMARY KEY,
            location TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def get_ip_location(ip):
    """获取 IP 归属地，先查缓存，未命中则查 API"""
    if ip in ("127.0.0.1", "::1", "localhost"):
        return "本地"

    conn = get_db()
    row = conn.execute("SELECT location FROM ip_cache WHERE ip = ?", (ip,)).fetchone()
    conn.close()
    if row:
        return row["location"]

    try:
        import urllib.request
        import json

        url = f"http://ip-api.com/json/{ip}?lang=zh-CN&fields=city,regionName,country"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        parts = []
        if data.get("country"):
            parts.append(data["country"])
        if data.get("regionName"):
            parts.append(data["regionName"])
        if data.get("city"):
            parts.append(data["city"])

        location = " ".join(parts) if parts else "未知"

        now = datetime.now(timezone.utc).isoformat()
        conn = get_db()
        conn.execute(
            "INSERT OR REPLACE INTO ip_cache (ip, location, updated_at) VALUES (?, ?, ?)",
            (ip, location, now),
        )
        conn.commit()
        conn.close()

        return location
    except Exception:
        return "未知"


def create_question(content, asker_cookie_id, asker_ip, parent_id=None):
    """创建新问题（或追问），返回 (question_id, secret_key)"""
    question_id = str(uuid.uuid4())
    secret = secrets.token_urlsafe(16)
    now = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    conn.execute(
        "INSERT INTO questions (id, content, asker_cookie_id, asker_ip, created_at, secret_key, parent_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (question_id, content, asker_cookie_id, asker_ip, now, secret, parent_id),
    )
    conn.commit()
    conn.close()
    return question_id, secret


def get_visible_questions():
    """获取所有公开展示的问答（顶级 + 仅已回答的追问），按回答时间倒序"""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, content, answer_content, created_at, answered_at, modified_at "
        "FROM questions "
        "WHERE is_answered = 1 AND is_visible = 1 AND parent_id IS NULL "
        "ORDER BY answered_at DESC"
    ).fetchall()
    questions = [dict(row) for row in rows]

    # 只加载已回答的追问（未回答的追问不在公开页显示）
    for q in questions:
        q["follow_ups"] = _get_follow_ups(conn, q["id"], answered_only=True)

    conn.close()
    return questions


def get_questions_by_cookie(asker_cookie_id):
    """根据 Cookie ID 获取用户的所有顶级问题及追问"""
    conn = get_db()
    # 顶级问题
    rows = conn.execute(
        "SELECT id, content, is_answered, answer_content, is_visible, created_at, "
        "answered_at, parent_id "
        "FROM questions "
        "WHERE asker_cookie_id = ? AND parent_id IS NULL "
        "ORDER BY created_at DESC",
        (asker_cookie_id,),
    ).fetchall()
    questions = [dict(row) for row in rows]

    # 为每个问题加载追问
    for q in questions:
        q["follow_ups"] = _get_follow_ups(conn, q["id"])
        # 检查是否有未回答的追问
        q["has_unanswered_followup"] = any(
            f["is_answered"] == 0 for f in q["follow_ups"]
        )

    conn.close()
    return questions


def _get_follow_ups(conn, parent_id, answered_only=False):
    """获取某个问题的追问，answered_only=True 时只返回已回答的"""
    if answered_only:
        rows = conn.execute(
            "SELECT id, content, is_answered, answer_content, created_at, answered_at, modified_at "
            "FROM questions WHERE parent_id = ? AND is_answered = 1 ORDER BY created_at ASC",
            (parent_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, content, is_answered, answer_content, created_at, answered_at, modified_at "
            "FROM questions WHERE parent_id = ? ORDER BY created_at ASC",
            (parent_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_follow_ups(parent_id):
    """获取某个问题的所有追问（公开调用）"""
    conn = get_db()
    result = _get_follow_ups(conn, parent_id)
    conn.close()
    return result


def get_all_questions(filter_type="all"):
    """管理员：获取所有顶级问题，支持筛选"""
    conn = get_db()
    base_query = "SELECT * FROM questions WHERE parent_id IS NULL "
    params = ()

    if filter_type == "unanswered":
        base_query += "AND is_answered = 0 "
    elif filter_type == "answered":
        base_query += "AND is_answered = 1 "
    elif filter_type == "visible":
        base_query += "AND is_visible = 1 "

    base_query += "ORDER BY created_at DESC"
    rows = conn.execute(base_query, params).fetchall()
    questions = [dict(row) for row in rows]

    # 为每个问题加载追问
    for q in questions:
        q["follow_ups"] = _get_follow_ups(conn, q["id"])
        q["has_unanswered_followup"] = any(
            f["is_answered"] == 0 for f in q["follow_ups"]
        )

    conn.close()
    return questions


def get_unanswered_count():
    """管理员：获取未回答问题总数（包含顶级问题 + 追问）"""
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) as count FROM questions WHERE is_answered = 0"
    ).fetchone()
    conn.close()
    return row["count"]


def update_question(question_id, answer_content=None, is_visible=None):
    """管理员：更新问题的回答和展示状态"""
    conn = get_db()
    now = datetime.now(timezone.utc).isoformat()

    if answer_content is not None:
        # 检查是否已经回答过（判断用 answered_at 还是 modified_at）
        existing = conn.execute(
            "SELECT is_answered, answer_content FROM questions WHERE id = ?",
            (question_id,),
        ).fetchone()

        if existing and existing["is_answered"]:
            # 已回答 → 这是修改，记录 modified_at
            conn.execute(
                "UPDATE questions SET answer_content = ?, modified_at = ? WHERE id = ?",
                (answer_content, now, question_id),
            )
        else:
            # 首次回答
            conn.execute(
                "UPDATE questions SET answer_content = ?, is_answered = 1, answered_at = ? WHERE id = ?",
                (answer_content, now, question_id),
            )

    if is_visible is not None:
        conn.execute(
            "UPDATE questions SET is_visible = ? WHERE id = ?",
            (1 if is_visible else 0, question_id),
        )

    conn.commit()
    conn.close()


def get_question_by_id(question_id):
    """根据 ID 获取单个问题"""
    conn = get_db()
    row = conn.execute("SELECT * FROM questions WHERE id = ?", (question_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_question_by_secret(question_id, secret_key):
    """根据问题 ID + 密钥获取单个问题（含追问）"""
    conn = get_db()
    row = conn.execute(
        "SELECT id, content, is_answered, answer_content, is_visible, created_at, answered_at, parent_id "
        "FROM questions WHERE id = ? AND secret_key = ?",
        (question_id, secret_key),
    ).fetchone()
    if not row:
        conn.close()
        return None
    question = dict(row)
    # 如果是顶级问题，加载所有追问（含未回答的）
    if not question.get("parent_id"):
        question["follow_ups"] = _get_follow_ups(conn, question["id"], answered_only=False)
        question["has_unanswered_followup"] = any(
            f["is_answered"] == 0 for f in question["follow_ups"]
        )
    conn.close()
    return question


def adopt_question(question_id, asker_cookie_id):
    """将问题关联到新的 cookie ID（通过私密链接认领）"""
    conn = get_db()
    conn.execute(
        "UPDATE questions SET asker_cookie_id = ? WHERE id = ?",
        (asker_cookie_id, question_id),
    )
    conn.commit()
    conn.close()


def count_recent_questions_from_ip(ip, minutes=1):
    """统计某 IP 在最近 N 分钟内的提问数"""
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) as count FROM questions WHERE asker_ip = ? AND created_at >= datetime('now', ?)",
        (ip, f"-{minutes} minutes"),
    ).fetchone()
    conn.close()
    return row["count"]
