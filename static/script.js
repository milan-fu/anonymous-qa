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
