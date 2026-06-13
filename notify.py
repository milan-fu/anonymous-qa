import os
import threading
import time

import requests

APP_ID = os.environ.get("FEISHU_APP_ID", "cli_a9409f28d1b99cc0")
APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
RECEIVE_ID = os.environ.get("FEISHU_RECEIVE_ID", "ou_74e0fa10801c21add8e58b962dfd3dc5")

_token = None
_token_expires = 0


def _get_token():
    """获取 tenant_access_token，缓存到过期"""
    global _token, _token_expires
    if _token and time.time() < _token_expires:
        return _token
    try:
        r = requests.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": APP_ID, "app_secret": APP_SECRET},
            timeout=10,
        )
        data = r.json()
        _token = data.get("tenant_access_token", "")
        _token_expires = time.time() + data.get("expire", 7200) - 60
        return _token
    except Exception:
        return ""


def notify(text):
    """异步发送飞书文本消息到指定用户"""
    if not APP_SECRET:
        return

    def _send():
        try:
            token = _get_token()
            if not token:
                return
            requests.post(
                "https://open.feishu.cn/open-apis/im/v1/messages",
                params={"receive_id_type": "open_id"},
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "receive_id": RECEIVE_ID,
                    "msg_type": "text",
                    "content": '{"text":"' + text + '"}',
                },
                timeout=5,
            )
        except Exception:
            pass

    threading.Thread(target=_send, daemon=True).start()
