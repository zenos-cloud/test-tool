"""Kết nối tới API chính thức của OKX (v5).

Tài liệu: https://www.okx.com/docs-v5/en/
Mỗi yêu cầu riêng tư phải được "ký" bằng secret key để OKX biết đúng là cậu.
"""
import base64
import hashlib
import hmac
import json
from datetime import datetime, timezone
from urllib.parse import urlencode

import requests

BASE_URL = "https://www.okx.com"


class OKXError(Exception):
    pass


def sign(timestamp: str, method: str, path: str, body: str, secret: str) -> str:
    """Tạo chữ ký theo quy định của OKX: base64(HMAC-SHA256(ts + method + path + body))."""
    message = f"{timestamp}{method.upper()}{path}{body}"
    digest = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


class OKXClient:
    def __init__(self, api_key="", secret_key="", passphrase="", demo=True, timeout=10):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.demo = demo
        self.timeout = timeout
        self.session = requests.Session()

    # ---------- phần lõi ----------
    def _request(self, method, path, params=None, body=None, private=True):
        if params:
            path = f"{path}?{urlencode(params)}"
        body_str = json.dumps(body) if body else ""
        headers = {"Content-Type": "application/json"}

        if self.demo:
            headers["x-simulated-trading"] = "1"  # báo OKX đây là tài khoản demo

        if private:
            if not (self.api_key and self.secret_key and self.passphrase):
                raise OKXError("Chưa có API key. Hãy điền vào file .env trước.")
            now = datetime.now(timezone.utc)
            ts = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"
            headers.update({
                "OK-ACCESS-KEY": self.api_key,
                "OK-ACCESS-SIGN": sign(ts, method, path, body_str, self.secret_key),
                "OK-ACCESS-TIMESTAMP": ts,
                "OK-ACCESS-PASSPHRASE": self.passphrase,
            })

        try:
            resp = self.session.request(method, BASE_URL + path, headers=headers,
                                        data=body_str or None, timeout=self.timeout)
            data = resp.json()
        except requests.RequestException as e:
            raise OKXError(f"Lỗi mạng: {e}") from e
        except ValueError as e:
            raise OKXError(f"OKX trả về dữ liệu lạ (HTTP {resp.status_code})") from e

        if data.get("code") != "0":
            detail = data.get("msg") or ""
            # Lệnh đặt sai thường có lý do chi tiết nằm trong data[0].sMsg
            if data.get("data") and isinstance(data["data"], list):
                detail = data["data"][0].get("sMsg") or detail
            raise OKXError(f"OKX báo lỗi {data.get('code')}: {detail}")
        return data.get("data", [])

    # ---------- dữ liệu công khai (không cần key) ----------
    def get_price(self, inst_id: str) -> float:
        data = self._request("GET", "/api/v5/market/ticker", {"instId": inst_id}, private=False)
        if not data:
            raise OKXError(f"Không tìm thấy cặp {inst_id}")
        return float(data[0]["last"])

    # ---------- tài khoản chính ----------
    def get_balance(self) -> dict:
        """Trả về {'total_usd': ..., 'coins': [(coin, số lượng, giá trị USD), ...]}"""
        data = self._request("GET", "/api/v5/account/balance")
        if not data:
            return {"total_usd": 0.0, "coins": []}
        acc = data[0]
        coins = []
        for d in acc.get("details", []):
            amount = float(d.get("eq") or 0)
            if amount > 0:
                coins.append((d["ccy"], amount, float(d.get("eqUsd") or 0)))
        coins.sort(key=lambda c: c[2], reverse=True)
        return {"total_usd": float(acc.get("totalEq") or 0), "coins": coins}

    # ---------- tài khoản phụ (của chính cậu) ----------
    def list_subaccounts(self) -> list:
        data = self._request("GET", "/api/v5/users/subaccount/list")
        return [d["subAcct"] for d in data]

    def get_subaccount_balance(self, sub_name: str) -> float:
        data = self._request("GET", "/api/v5/account/subaccount/balances", {"subAcct": sub_name})
        return float(data[0].get("totalEq") or 0) if data else 0.0

    # ---------- đặt lệnh ----------
    def market_buy_usdt(self, inst_id: str, usdt_amount: float, max_usdt: float) -> str:
        """Mua theo giá thị trường bằng một số USDT cố định. Trả về mã lệnh."""
        if usdt_amount <= 0:
            raise OKXError("Số tiền phải lớn hơn 0")
        if usdt_amount > max_usdt:
            raise OKXError(f"Từ chối: {usdt_amount} USDT vượt giới hạn an toàn {max_usdt} USDT")
        body = {
            "instId": inst_id,
            "tdMode": "cash",          # giao dịch spot, không đòn bẩy
            "side": "buy",
            "ordType": "market",
            "sz": str(usdt_amount),
            "tgtCcy": "quote_ccy",     # sz tính bằng USDT
        }
        data = self._request("POST", "/api/v5/trade/order", body=body)
        return data[0]["ordId"]
