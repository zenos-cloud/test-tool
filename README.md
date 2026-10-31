# OKX Helper 🤖

Trợ lý hằng ngày cho **tài khoản OKX của chính cậu** (tài khoản chính + tài khoản phụ chính chủ).
Dùng trên **máy tính** (gõ lệnh) và **điện thoại** (qua Telegram).

## Tool làm được gì?
| Chức năng | Mô tả |
|---|---|
| 📊 Xem số dư | Tài khoản chính + tất cả tài khoản phụ, cộng tổng |
| 💲 Xem giá | `/price BTC`, `/price ETH-USDT` |
| 📝 Danh sách việc hằng ngày | Tự nhắc cậu check-in, làm nhiệm vụ... (tool chỉ **nhắc**, cậu tự làm) |
| ☀️ Báo cáo buổi sáng | Tự gửi số dư + việc cần làm lúc 8:00 |
| ⏰ Nhắc việc buổi tối | Lúc 20:00 nếu còn việc chưa xong |
| 🛒 Mua định kỳ (DCA) | Mua một số USDT cố định mỗi ngày. **Mặc định TẮT**, có giới hạn an toàn |

## ⚠️ Quy tắc an toàn (đọc trước!)
1. **Chỉ dùng cho tài khoản của chính cậu.** Không dùng để quản lý nhiều tài khoản farm điểm, vì OKX cấm và có thể khóa hết.
2. API key **chỉ bật quyền Đọc + Giao dịch**, **KHÔNG bật Rút tiền**.
3. Thử ở **chế độ DEMO** trước (`OKX_DEMO=1`), tiền ảo nên không mất gì.
4. **Không bao giờ** gửi file `.env` cho ai hay đưa lên mạng.

---

## Cài đặt từng bước (Windows)

### Bước 1: Cài Python
Tải tại https://www.python.org/downloads/ và khi cài **nhớ tick ô "Add Python to PATH"**.

### Bước 2: Tải thư mục này về máy
Mở thư mục `okx-helper`, nhấn chuột phải vào chỗ trống, chọn **Open in Terminal**.

### Bước 3: Cài thư viện
```
pip install -r requirements.txt
```

### Bước 4: Tạo API key DEMO trên OKX
1. Vào OKX (web) → **Trade** → **Demo trading** (Giao dịch demo).
2. Trong chế độ demo: **Hồ sơ → Demo trading API** → **Create API key**.
3. Quyền: **Read** + **Trade**. Đặt passphrase (mật khẩu riêng cho API, nhớ ghi lại).
4. Lưu lại 3 thứ: **API key**, **Secret key**, **Passphrase**.

### Bước 5: Điền cấu hình (cách dễ nhất)
```
python main.py setup
```
Tool sẽ hỏi lần lượt API key, Secret key, Passphrase, tự lưu file `.env` và thử kết nối luôn.
(Khi dán Secret key và Passphrase chữ sẽ không hiện ra, đó là bình thường.)

### Bước 6: Chạy thử trên máy tính
```
python main.py balance
python main.py price BTC
python main.py tasks
python main.py done 1
```

---

## Dùng trên điện thoại (Telegram)

1. Mở Telegram, tìm **@BotFather**, gõ `/newbot`, đặt tên và nhận **token**.
2. Dán token vào `.env`: `TELEGRAM_BOT_TOKEN=...`
3. Chạy: `python main.py bot`
4. Mở bot của cậu trên Telegram, gõ `/myid`, rồi dán số nhận được vào `TELEGRAM_CHAT_ID=...` trong `.env`.
5. Tắt bot (Ctrl+C) rồi chạy lại `python main.py bot`. Xong! Gõ `/help` để xem lệnh.

> Bot chỉ chạy khi máy tính đang bật. Muốn chạy 24/7 thì cần thuê một máy chủ nhỏ (VPS), tính sau.

**Các lệnh Telegram:** `/balance` `/price BTC` `/tasks` `/done 1` `/dca` (rồi `/yes`) `/status` `/help`

---

## Tùy chỉnh
- **Việc hằng ngày:** sửa file `tasks.json`.
- **Giờ báo cáo / nhắc:** `DAILY_REPORT_TIME`, `REMINDER_TIME` trong `.env`.
- **Mua định kỳ:** `DCA_ENABLED=1`, `DCA_PAIR`, `DCA_AMOUNT_USDT`, `DCA_TIME`. Mọi lệnh lớn hơn `MAX_ORDER_USDT` sẽ bị từ chối.
- **Chuyển sang tiền thật:** tạo API key thật (không bật Rút tiền) rồi đặt `OKX_DEMO=0`. Chỉ làm khi đã thử demo kỹ.

## Cấu trúc file
```
main.py        ← chạy chương trình (máy tính + Telegram)
core.py        ← các chức năng: số dư, việc hằng ngày, DCA, lịch
okx_client.py  ← kết nối API chính thức của OKX
config.py      ← đọc file .env
tasks.json     ← danh sách việc hằng ngày
```
