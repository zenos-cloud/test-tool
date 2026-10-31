"""OKX Helper - trợ lý hằng ngày cho tài khoản OKX của cậu.

Cách dùng trên máy tính:
    python main.py setup            # cài đặt nhanh (nhập key)
    python main.py balance          # xem số dư
    python main.py price BTC        # xem giá
    python main.py tasks            # xem việc hôm nay
    python main.py done 1           # đánh dấu việc số 1 đã xong
    python main.py bot              # chạy bot Telegram (dùng trên điện thoại)
"""
import sys
import time

import requests

import config
import core

HELP_TEXT = """🤖 OKX Helper - các lệnh:
/balance - số dư tài khoản chính + phụ
/price BTC - xem giá
/tasks - việc cần làm hôm nay
/done 1 - đánh dấu việc số 1 xong
/dca - mua định kỳ ngay (cần xác nhận)
/status - chế độ và lịch hiện tại
/myid - xem chat ID của cậu"""


# ===================== Telegram =====================
class TelegramBot:
    def __init__(self, token: str, chat_id: str):
        self.api = f"https://api.telegram.org/bot{token}"
        self.chat_id = str(chat_id)
        self.offset = 0
        self.pending_dca = False
        self.client = core.make_client()

    def send(self, text: str, chat_id: str = None):
        try:
            requests.post(f"{self.api}/sendMessage",
                          json={"chat_id": chat_id or self.chat_id, "text": text}, timeout=10)
        except requests.RequestException as e:
            print("Không gửi được tin Telegram:", e)

    def get_updates(self):
        try:
            r = requests.get(f"{self.api}/getUpdates",
                             params={"offset": self.offset, "timeout": 30}, timeout=40)
            return r.json().get("result", [])
        except (requests.RequestException, ValueError):
            time.sleep(5)
            return []

    def handle(self, chat_id: str, text: str):
        parts = text.strip().split()
        cmd = parts[0].lower().split("@")[0] if parts else ""
        args = parts[1:]

        if cmd == "/myid":
            return self.send(f"Chat ID của cậu: {chat_id}\nDán số này vào TELEGRAM_CHAT_ID trong .env", chat_id)

        # Chỉ chủ tài khoản mới được ra lệnh
        if chat_id != self.chat_id:
            return self.send("⛔ Cậu không có quyền dùng bot này.", chat_id)

        if cmd in ("/start", "/help"):
            self.send(HELP_TEXT)
        elif cmd == "/balance":
            self.send("⏳ Đang lấy số dư...")
            self.send(core.balance_report(self.client))
        elif cmd == "/price":
            self.send(core.price_report(self.client, args[0] if args else "BTC"))
        elif cmd == "/tasks":
            self.send(core.tasks_report())
        elif cmd == "/done":
            if not args or not args[0].isdigit():
                return self.send("Gõ kiểu: /done 1")
            self.send(core.mark_done(int(args[0])))
        elif cmd == "/dca":
            self.pending_dca = True
            self.send(f"Mua {config.DCA_AMOUNT_USDT} USDT {config.DCA_PAIR} ({core.mode_label()})?\n"
                      f"Gõ /yes để xác nhận, lệnh khác để hủy.")
            return
        elif cmd == "/yes" and self.pending_dca:
            self.send(core.run_dca(self.client))
        elif cmd == "/status":
            self.send(status_text())
        else:
            self.send("Không hiểu lệnh. Gõ /help")
        self.pending_dca = False

    def run_scheduled(self):
        for job in core.due_jobs():
            if job == "report":
                self.send("☀️ Báo cáo buổi sáng\n\n" + core.balance_report(self.client)
                          + "\n\n" + core.tasks_report())
            elif job == "reminder":
                report = core.tasks_report()
                if "Xong hết" not in report:
                    self.send("⏰ Nhắc việc buổi tối\n\n" + report)
            elif job == "dca":
                self.send(core.run_dca(self.client))

    def run(self):
        print(f"Bot đang chạy ({core.mode_label()}). Nhấn Ctrl+C để dừng.")
        if self.chat_id:
            self.send("✅ OKX Helper đã bật.\n" + status_text())
        while True:
            for upd in self.get_updates():
                self.offset = upd["update_id"] + 1
                msg = upd.get("message") or {}
                if "text" in msg:
                    self.handle(str(msg["chat"]["id"]), msg["text"])
            if self.chat_id:
                self.run_scheduled()


def status_text() -> str:
    dca = (f"BẬT: {config.DCA_AMOUNT_USDT} USDT {config.DCA_PAIR} lúc {config.DCA_TIME}"
           if config.DCA_ENABLED else "TẮT")
    return (f"Chế độ: {core.mode_label()}\n"
            f"Báo cáo sáng: {config.DAILY_REPORT_TIME}\n"
            f"Nhắc việc tối: {config.REMINDER_TIME}\n"
            f"Mua định kỳ: {dca}\n"
            f"Giới hạn mỗi lệnh: {config.MAX_ORDER_USDT} USDT")


# ===================== Cài đặt nhanh =====================
def setup_wizard():
    """Hỏi từng thông tin, tự ghi file .env rồi thử kết nối OKX."""
    from getpass import getpass
    from okx_client import OKXClient

    print("=== Cài đặt OKX Helper ===")
    print("Khi dán Secret key và Passphrase, chữ sẽ KHÔNG hiện ra (để bảo mật) - cứ dán rồi Enter.\n")
    api_key = input("1) Dán API key: ").strip()
    secret = getpass("2) Dán Secret key: ").strip()
    passphrase = getpass("3) Gõ Passphrase: ").strip()
    demo = input("4) Đây là key DEMO? (Enter = có, gõ n = tiền thật): ").strip().lower() != "n"
    tg_token = input("5) Telegram bot token (Enter để bỏ qua): ").strip()

    print("\n⏳ Đang thử kết nối OKX...")
    try:
        bal = OKXClient(api_key, secret, passphrase, demo=demo).get_balance()
        print(f"✅ Kết nối thành công! Số dư: ${bal['total_usd']:,.2f}")
    except Exception as e:
        print(f"❌ Chưa kết nối được: {e}")
        if input("Vẫn lưu cấu hình? (y/N): ").strip().lower() != "y":
            print("Chưa lưu gì. Kiểm tra lại key rồi chạy lại: python main.py setup")
            return 1

    env_path = config.BASE_DIR / ".env"
    template = (config.BASE_DIR / ".env.example").read_text(encoding="utf-8")
    values = {"OKX_API_KEY": api_key, "OKX_SECRET_KEY": secret, "OKX_PASSPHRASE": passphrase,
              "OKX_DEMO": "1" if demo else "0"}
    if tg_token:
        values["TELEGRAM_BOT_TOKEN"] = tg_token
    lines = []
    for line in template.splitlines():
        key = line.split("=", 1)[0].strip()
        lines.append(f"{key}={values[key]}" if key in values and "=" in line else line)
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"💾 Đã lưu vào {env_path}")
    print("Tiếp theo: python main.py balance" + ("   hoặc   python main.py bot" if tg_token else ""))
    return 0


# ===================== Dòng lệnh trên máy tính =====================
def main(argv):
    if len(argv) > 1 and argv[1] == "setup":
        return setup_wizard()
    cmd = argv[1] if len(argv) > 1 else "help"
    client = core.make_client()

    if cmd == "balance":
        print(core.balance_report(client))
    elif cmd == "price":
        print(core.price_report(client, argv[2] if len(argv) > 2 else "BTC"))
    elif cmd == "tasks":
        print(core.tasks_report())
    elif cmd == "done" and len(argv) > 2 and argv[2].isdigit():
        print(core.mark_done(int(argv[2])))
    elif cmd == "status":
        print(status_text())
    elif cmd == "bot":
        if not config.TELEGRAM_BOT_TOKEN:
            print("Thiếu TELEGRAM_BOT_TOKEN trong file .env")
            return 1
        if not config.TELEGRAM_CHAT_ID:
            print("Chưa có TELEGRAM_CHAT_ID: bot vẫn chạy, hãy nhắn /myid cho bot để lấy số.")
        TelegramBot(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID).run()
    else:
        print(__doc__)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except KeyboardInterrupt:
        print("\nĐã dừng.")
