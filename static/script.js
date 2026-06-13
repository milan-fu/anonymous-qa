/* ── 卡片折叠 / 展开 ────────────────────────────────── */

function toggleCard(header) {
    const card = header.parentElement;
    card.classList.toggle('expanded');
}

/* ── 提问模态框 ──────────────────────────────────────── */

function openAskModal() {
    document.getElementById('askModal').classList.add('active');
    document.getElementById('questionInput').focus();
}

function closeAskModal() {
    document.getElementById('askModal').classList.remove('active');
    document.getElementById('questionInput').value = '';
    document.getElementById('charCount').textContent = '0';
}

// 关闭模态框：点击背景
document.addEventListener('click', function (e) {
    const modal = document.getElementById('askModal');
    if (modal && e.target === modal) {
        closeAskModal();
    }
});

// ESC 关闭
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        closeAskModal();
    }
});

// 字数统计
document.addEventListener('DOMContentLoaded', function () {
    const input = document.getElementById('questionInput');
    const counter = document.getElementById('charCount');

    if (input && counter) {
        input.addEventListener('input', function () {
            const len = this.value.length;
            counter.textContent = len;
            if (len > 180) {
                counter.classList.add('over');
            } else {
                counter.classList.remove('over');
            }
        });
    }
});

/* ── 提交问题 ───────────────────────────────────────── */

async function submitQuestion() {
    const input = document.getElementById('questionInput');
    const content = input.value.trim();

    if (!content) {
        showToast('请输入问题内容', 'error');
        return;
    }

    if (content.length > 200) {
        showToast('问题不能超过 200 字', 'error');
        return;
    }

    try {
        const res = await fetch('/api/questions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });

        const data = await res.json();

        if (res.ok) {
            // 关闭提问弹窗，显示成功弹窗
            document.getElementById('askModal').classList.remove('active');
            document.getElementById('secretUrl').value = data.view_url;
            document.getElementById('successModal').classList.add('active');
            // 自动复制（HTTP 兼容）
            copyToClipboard(data.view_url);
        } else {
            showToast(data.error || '提交失败', 'error');
        }
    } catch (err) {
        showToast('网络错误，请重试', 'error');
    }
}

function closeSuccessModal() {
    document.getElementById('successModal').classList.remove('active');
    document.getElementById('questionInput').value = '';
    document.getElementById('charCount').textContent = '0';
}

function copyToClipboard(text) {
    // 优先用 Clipboard API（HTTPS），fallback 到 execCommand（HTTP）
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).catch(function() {});
    } else {
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.left = '-9999px';
        ta.style.top = '-9999px';
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        try { document.execCommand('copy'); } catch {}
        document.body.removeChild(ta);
    }
}

function copySecretUrl() {
    var input = document.getElementById('secretUrl');
    copyToClipboard(input.value);
    showToast('链接已复制！', 'success');
}

/* ── 关闭成功弹窗：点击背景 ────────────────────────────── */

document.addEventListener('click', function (e) {
    const successModal = document.getElementById('successModal');
    if (successModal && e.target === successModal) {
        // 不允许点背景关闭，必须点按钮
    }
});

/* ── QA 详情弹窗（公开页） ─────────────────────────────── */

var qaData = [];

async function loadQaData() {
    try {
        var res = await fetch('/api/questions/visible');
        var newData = await res.json();
        if (JSON.stringify(newData) !== JSON.stringify(qaData)) {
            qaData = newData;
            renderQaList();
        }
    } catch(e) {}
}

function renderQaList() {
    var list = document.getElementById('qaList');
    var title = document.querySelector('.section-title');
    if (title) title.textContent = '— 已公开的回答 · ' + qaData.length + ' 个问题 —';
    if (!list) return;
    if (!qaData.length) {
        list.innerHTML = '<div class="empty-state"><p>还没有公开的回答，快来提问吧！</p></div>';
        return;
    }
    list.innerHTML = qaData.map(function(q) {
        var pinBadge = '';
        if (q.is_help) {
            pinBadge = '<span class="pin-badge" style="background:#dbeafe;color:#1e40af;">📖 帮助</span>';
        } else if (q.is_pinned) {
            pinBadge = '<span class="pin-badge">📌 置顶</span>';
        }
        var tagBadge = q.tag ? '<span class="pin-badge" style="background:#e8f5e9;color:#2e7d32;">' + escapeHtml(q.tag) + '</span>' : '';
        return '<div class="qa-card qa-clickable' + (q.is_pinned ? ' qa-pinned' : '') + '" onclick="openQaDetail(\'' + q.id + '\')">' +
            '<div class="qa-card-header">' +
                pinBadge +
                tagBadge +
                '<span class="qa-card-question">Q: ' + escapeHtml(q.content) + '</span>' +
            '</div>' +
        '</div>';
    }).join('');
}

loadQaData();

// 每 10 秒自动刷新
setInterval(loadQaData, 10000);

function openQaDetail(qid) {
    var q = qaData.find(function(x) { return x.id === qid; });
    if (!q) return;

    var followUpsHtml = '';
    if (q.follow_ups && q.follow_ups.length > 0) {
        followUpsHtml = '<div class="follow-ups">' +
            q.follow_ups.map(function(fu) {
                return '<div class="follow-up-item">' +
                    '<div class="follow-up-q">🙋 追问：' + escapeHtml(fu.content) + '</div>' +
                    '<div class="follow-up-time">📅 ' + formatTimeStr(fu.created_at) + '</div>' +
                    '<div class="follow-up-a">💬 ' + escapeHtml(fu.answer_content) + '</div>' +
                    '<div class="follow-up-ans-time">' + (fu.modified_at ? '📝 最后修改 ' + formatTimeStr(fu.modified_at) : '💬 回答时间 ' + formatTimeStr(fu.answered_at)) + '</div>' +
                '</div>';
            }).join('') +
        '</div>';
    }

    var html =
        '<div class="modal-header">' +
            '<h3>问答详情' + (q.is_pinned ? ' <span class="pin-badge">📌 置顶</span>' : '') + '</h3>' +
            '<button class="modal-close" onclick="closeQaDetail()">&times;</button>' +
        '</div>' +
        '<div class="modal-body">' +
            '<div class="detail-meta">' +
                '<span>📅 提问 ' + formatTimeStr(q.created_at) + '</span>' +
                '<span>💬 回答 ' + formatTimeStr(q.answered_at) + '</span>' +
            '</div>' +
            '<div class="detail-question">' + escapeHtml(q.content) + '</div>' +
            '<div class="qa-card-answer" style="margin:0;padding:12px 0;border:none;">' + escapeHtml(q.answer_content) + '</div>' +
            followUpsHtml +
        '</div>';
    document.getElementById('qaDetailContent').innerHTML = html;
    document.getElementById('qaDetailModal').classList.add('active');
}

function closeQaDetail() {
    document.getElementById('qaDetailModal').classList.remove('active');
}

function formatTimeStr(isoStr) {
    if (!isoStr) return '';
    var d = new Date(isoStr);
    var pad = function(n) { return n < 10 ? '0' + n : n; };
    return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate())
        + ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
}

function escapeHtml(str) {
    var div = document.createElement('div');
    div.textContent = str || '';
    return div.innerHTML;
}

// 点击背景关闭
document.addEventListener('click', function(e) {
    var m = document.getElementById('qaDetailModal');
    if (m && e.target === m) closeQaDetail();
});

/* ── Toast 提示 ─────────────────────────────────────── */

let toastTimer;

function showToast(message, type) {
    const toast = document.getElementById('toast');
    if (!toast) return;

    toast.textContent = message;
    toast.className = `toast ${type} show`;

    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
        toast.classList.remove('show');
    }, 2500);
}
