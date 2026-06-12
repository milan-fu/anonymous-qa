import uuid
from functools import wraps

from flask import (
    Flask,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

import config
import database

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# 确保 data 目录存在
import os

os.makedirs(os.path.dirname(config.DATABASE_PATH), exist_ok=True)

# 初始化数据库
with app.app_context():
    database.init_db()


# ── 工具函数 ─────────────────────────────────────────────


def get_real_ip():
    """获取真实客户端 IP（处理 Nginx 反向代理）"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr


def get_or_create_asker_id():
    """获取或创建提问者的匿名 Cookie ID"""
    asker_id = request.cookies.get("asker_id")
    if not asker_id:
        asker_id = str(uuid.uuid4())
    return asker_id


def admin_required(f):
    """装饰器：要求管理员已登录"""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "未授权"}), 401
            return redirect(url_for("admin_login_page"))
        return f(*args, **kwargs)

    return decorated


def set_asker_cookie(response):
    """为响应设置匿名 Cookie（如尚未设置）"""
    if not request.cookies.get("asker_id"):
        asker_id = str(uuid.uuid4())
        response.set_cookie(
            "asker_id",
            asker_id,
            max_age=60 * 60 * 24 * 365 * 10,  # 10 年，基本永不过期
            httponly=True,
            samesite="Lax",
        )
    return response


# ── 页面路由 ─────────────────────────────────────────────


@app.route("/")
def index():
    """公开提问 & 浏览页"""
    questions = database.get_visible_questions()
    response = app.make_response(
        render_template("index.html", questions=questions)
    )
    return set_asker_cookie(response)


@app.route("/my")
def my_questions_page():
    """「我的问题」页面"""
    asker_id = request.cookies.get("asker_id")
    questions = database.get_questions_by_cookie(asker_id) if asker_id else []
    response = app.make_response(
        render_template("my.html", questions=questions)
    )
    return set_asker_cookie(response)


@app.route("/admin")
def admin_login_page():
    """管理员登录页面"""
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_login.html")


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    """管理员面板"""
    return render_template("admin.html")


@app.route("/q/<question_id>")
def view_question(question_id):
    """通过私密链接查看单个问题"""
    secret_key = request.args.get("key", "")
    question = database.get_question_by_secret(question_id, secret_key)
    if not question:
        return render_template("question_not_found.html"), 404
    return render_template("question_detail.html", question=question)


# ── 公开 API ─────────────────────────────────────────────


@app.route("/api/questions/visible")
def api_visible_questions():
    """获取公开的问答列表"""
    questions = database.get_visible_questions()
    return jsonify(questions)


@app.route("/api/questions", methods=["POST"])
def api_create_question():
    """提交新问题"""
    data = request.get_json()
    if not data or not data.get("content"):
        return jsonify({"error": "问题内容不能为空"}), 400

    content = data["content"].strip()
    if len(content) > config.QUESTION_MAX_LENGTH:
        return jsonify({"error": f"问题不能超过 {config.QUESTION_MAX_LENGTH} 字"}), 400

    # IP 频率限制
    asker_ip = get_real_ip()
    recent_count = database.count_recent_questions_from_ip(asker_ip, minutes=1)
    if recent_count >= config.RATE_LIMIT_PER_MINUTE:
        return jsonify({"error": "提问太频繁了，请稍后再试"}), 429

    asker_id = get_or_create_asker_id()
    question_id, secret_key = database.create_question(content, asker_id, asker_ip)

    view_url = url_for("view_question", question_id=question_id, _external=True)
    response = jsonify({
        "success": True,
        "question_id": question_id,
        "secret_key": secret_key,
        "view_url": f"{view_url}?key={secret_key}",
    })
    return set_asker_cookie(response)


# ── 匿名用户 API ─────────────────────────────────────────


@app.route("/api/my-questions")
def api_my_questions():
    """获取当前 Cookie 对应的所有问题"""
    asker_id = request.cookies.get("asker_id")
    if not asker_id:
        return jsonify([])
    questions = database.get_questions_by_cookie(asker_id)
    return jsonify(questions)


# ── 管理员 API ────────────────────────────────────────────


@app.route("/api/admin/login", methods=["POST"])
def api_admin_login():
    """管理员登录"""
    data = request.get_json()
    if not data or not data.get("password"):
        return jsonify({"error": "请输入密码"}), 400

    if data["password"] == config.ADMIN_PASSWORD:
        session["admin_logged_in"] = True
        return jsonify({"success": True})

    return jsonify({"error": "密码错误"}), 401


@app.route("/api/admin/logout", methods=["POST"])
def api_admin_logout():
    """管理员退出"""
    session.pop("admin_logged_in", None)
    return jsonify({"success": True})


@app.route("/api/admin/questions")
@admin_required
def api_admin_questions():
    """管理员获取所有问题（支持筛选）"""
    filter_type = request.args.get("filter", "all")
    questions = database.get_all_questions(filter_type)

    # 为每个问题附加 IP 归属地
    for q in questions:
        q["asker_location"] = database.get_ip_location(q["asker_ip"])

    return jsonify(questions)


@app.route("/api/admin/questions/<question_id>", methods=["PUT"])
@admin_required
def api_admin_update_question(question_id):
    """管理员更新问题（回答、展示状态）"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "无效请求"}), 400

    answer_content = data.get("answer_content")
    is_visible = data.get("is_visible")

    database.update_question(
        question_id,
        answer_content=answer_content,
        is_visible=is_visible,
    )

    # 返回更新后的问题
    question = database.get_question_by_id(question_id)
    return jsonify({"success": True, "question": question})


# ── 启动入口 ─────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
