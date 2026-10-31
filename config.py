"""Đọc cấu hình từ file .env (không cần cài thêm thư viện)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _load_env_file(path: Path) -> None:
    """Đọc từng dòng KEY=VALUE trong .env và đưa vào biến môi trường."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


_load_env_file(BASE_DIR / ".env")


def get(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def get_bool(name: str, default: bool = False) -> bool:
    return get(name, "1" if default else "0") in ("1", "true", "yes", "on")


def get_float(name: str, default: float) -> float:
    try:
        return float(get(name, str(default)))
    except ValueError:
        return default


OKX_API_KEY = get("OKX_API_KEY")
OKX_SECRET_KEY = get("OKX_SECRET_KEY")
OKX_PASSPHRASE = get("OKX_PASSPHRASE")
OKX_DEMO = get_bool("OKX_DEMO", True)  # mặc định là demo cho an toàn

TELEGRAM_BOT_TOKEN = get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = get("TELEGRAM_CHAT_ID")

TIMEZONE_OFFSET = int(get_float("TIMEZONE_OFFSET", 7))
DAILY_REPORT_TIME = get("DAILY_REPORT_TIME", "08:00")
REMINDER_TIME = get("REMINDER_TIME", "20:00")

DCA_ENABLED = get_bool("DCA_ENABLED", False)
DCA_PAIR = get("DCA_PAIR", "BTC-USDT")
DCA_AMOUNT_USDT = get_float("DCA_AMOUNT_USDT", 5)
DCA_TIME = get("DCA_TIME", "09:00")
MAX_ORDER_USDT = get_float("MAX_ORDER_USDT", 20)

TASKS_FILE = BASE_DIR / "tasks.json"
STATE_FILE = BASE_DIR / "state.json"


def has_okx_keys() -> bool:
    return bool(OKX_API_KEY and OKX_SECRET_KEY and OKX_PASSPHRASE)
