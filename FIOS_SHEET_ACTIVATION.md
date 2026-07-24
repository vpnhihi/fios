# Fios — Kích hoạt license (Google Sheet)

## Trang kích hoạt (Sheet)
https://docs.google.com/spreadsheets/d/1cnfHaeZc1SfDCQZGWI4CDV3vXIT6kGxgCCbVwhPGyno/edit?gid=0#gid=0

CSV (app/tool đọc):
https://docs.google.com/spreadsheets/d/1cnfHaeZc1SfDCQZGWI4CDV3vXIT6kGxgCCbVwhPGyno/export?format=csv&gid=0

Sheet ID: `1cnfHaeZc1SfDCQZGWI4CDV3vXIT6kGxgCCbVwhPGyno`
GID: `0`

## Cột gợi ý (giống HZalo sheet license)
| Cột | Ý nghĩa |
|-----|---------|
| A | STT |
| B | TÀI KHOẢN |
| C | MẬT KHẨU / KEY |
| D | HẠN (số ngày) |
| E | ID KHÁCH |
| F | ID MÁY (trống = máy mới) |
| G | TRẠNG THÁI: CHẠY / DỪNG |
| H | SỬ DỤNG ĐẾN NGÀY |

Share sheet: **Anyone with the link → Viewer** (hoặc editor nếu tự ghi máy).

## Ghi chú kỹ thuật
- Payload engine vẫn là ChangeInfoIos dylib (path `/var/jb/etc/changeinfoios`, filter ChangeInfoIosMG/CT) để **không gãy inject**.
- Tên hiển thị app / package = **Fios Faker v3**.
- License HIOS gốc: `license.plist` + HWID local; sheet này là **trang kích hoạt Fios** (quản lý key/acc).

Env (nếu dùng bridge PC):
```
FIOS_SHEET_ID=1cnfHaeZc1SfDCQZGWI4CDV3vXIT6kGxgCCbVwhPGyno
FIOS_SHEET_GID=0
```
