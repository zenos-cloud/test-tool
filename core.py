"""Các chức năng chính. Dùng chung cho cả máy tính (CLI) lẫn Telegram."""
import json
from datetime import datetime, timedelta, timezone

import config
from okx_client import OKXClient, OKXError


def make_client() -> OKXClient:
    return OKXClient(config.OKX_API_KEY, config.OKX_SECRET_KEY,
                     config.OKX_PASSPHRASE, demo=config.OKX_DEMO)


def now_local() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=config.TIMEZONE_OFFSET)


def today_str() -> str:
    return now_local().strftime("%Y-%m-%d")


def mode_label() -> str:
    return "🧪 DEMO" if config.OKX_DEMO else "💰 TIỀN THẬT"


# ---------- lưu trạng thái (việc đã làm, lần chạy cuối) ----------
def load_state() -> dict:
    try:
        return json.loads(config.STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}


def save_state(state: dict) -> None:
    config.STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------- báo cáo số dư ----------
def balance_report(client: OKXClient) -> str:
    lines = [f"📊 Số dư ({mode_label()})"]
    try:
        bal = client.get_balance()
        lines.append(f"Tài khoản chính: ${bal['total_usd']:,.2f}")
        for coin, amount, usd in bal["coins"][:10]:
            lines.append(f"  • {coin}: {amount:g} (~${usd:,.2f})")
    except OKXError as e:
        return f"❌ {e}"

    total = bal["total_usd"]
    try:
        subs = client.list_subaccounts()
        if subs:
            lines.append("Tài khoản phụ:")
            for name in subs:
                try:
                    v = client.get_subaccount_balance(name)
                    total += v
                    lines.append(f"  • {name}: ${v:,.2f}")
                except OKXError as e:
                    lines.append(f"  • {name}: lỗi ({e})")
    except OKXError:
        lines.append("(Không đọc được tài khoản phụ. Demo thường không hỗ trợ.)")

    lines.append(f"➡️ Tổng: ${total:,.2f}")
    return "\n".join(lines)


def price_report(client: OKXClient, inst_id: str) -> str:
    inst_id = inst_id.upper()
    if "-" not in inst_id:
        inst_id += "-USDT"
    try:
        return f"💲 {inst_id}: {client.get_price(inst_id):,.4f}"
    except OKXError as e:
        return f"❌ {e}"


# ---------- danh sách việc hằng ngày ----------
def load_tasks() -> list:
    try:
        return json.loads(config.TASKS_FILE.read_text(encoding="utf-8")).get("tasks", [])
    except (FileNotFoundError, ValueError):
        return []


def tasks_report() -> str:
    tasks = load_tasks()
    if not tasks:
        return "Chưa có việc nào. Hãy sửa file tasks.json."
    done = set(load_state().get("done", {}).get(today_str(), []))
    lines = [f"📝 Việc hôm nay ({today_str()}):"]
    for i, t in enumerate(tasks, 1):
        lines.append(f"{'✅' if i in done else '⬜'} {i}. {t}")
    left = len(tasks) - len(done & set(range(1, len(tasks) + 1)))
    lines.append("🎉 Xong hết rồi!" if left == 0 else f"Còn {left} việc. Gõ /done <số> khi làm xong.")
    return "\n".join(lines)


def mark_done(number: int) -> str:
    tasks = load_tasks()
    if not 1 <= number <= len(tasks):
        return f"Số không hợp lệ. Chọn từ 1 đến {len(tasks)}."
    state = load_state()
    done_today = set(state.setdefault("done", {}).get(today_str(), []))
    done_today.add(number)
    # chỉ giữ lịch sử 7 ngày gần nhất cho file gọn
    state["done"] = {k: v for k, v in state["done"].items() if k >= (now_local() - timedelta(days=7)).strftime("%Y-%m-%d")}
    state["done"][today_str()] = sorted(done_today)
    save_state(state)
    return tasks_report()


# ---------- mua định kỳ (DCA) ----------
def run_dca(client: OKXClient) -> str:
    try:
        ord_id = client.market_buy_usdt(config.DCA_PAIR, config.DCA_AMOUNT_USDT, config.MAX_ORDER_USDT)
        return f"🛒 ({mode_label()}) Đã mua {config.DCA_AMOUNT_USDT} USDT {config.DCA_PAIR}. Mã lệnh: {ord_id}"
    except OKXError as e:
        return f"❌ Mua thất bại: {e}"


# ---------- lịch tự động ----------
def due_jobs() -> list:
    """Trả về danh sách việc đến giờ chạy hôm nay mà chưa chạy."""
    state = load_state()
    last = state.setdefault("last_run", {})
    hhmm = now_local().strftime("%H:%M")
    jobs = []
    schedule = {"report": config.DAILY_REPORT_TIME, "reminder": config.REMINDER_TIME}
    if config.DCA_ENABLED:
        schedule["dca"] = config.DCA_TIME
    for name, at in schedule.items():
        if hhmm >= at and last.get(name) != today_str():
            jobs.append(name)
            last[name] = today_str()
    if jobs:
        save_state(state)
    return jobs
