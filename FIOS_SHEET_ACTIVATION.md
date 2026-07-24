# Fios — Kích hoạt license (Google Sheet)

**Version:** 4.2.6-fios.3+

App **Fios** dùng **cùng engine license iPFaker 2.18.3+**: đọc Sheet CSV, **chỉ bắt buộc cột B + E**.

## Trang kích hoạt (Sheet)
https://docs.google.com/spreadsheets/d/1cnfHaeZc1SfDCQZGWI4CDV3vXIT6kGxgCCbVwhPGyno/edit?gid=0#gid=0

CSV (app đọc):
https://docs.google.com/spreadsheets/d/1cnfHaeZc1SfDCQZGWI4CDV3vXIT6kGxgCCbVwhPGyno/export?format=csv&gid=0

## Cột (đúng sheet “Kích iPFaker”)

| Cột | Header | Bắt buộc | App |
|-----|--------|----------|-----|
| A | STT | Không | Bỏ qua |
| **B** | **Key** | **Có** | Key đăng nhập |
| C | Hạn sử dụng | Không | Optional số ngày; trống = không giới hạn |
| D | ID MÁY | **Không** | **Bỏ** — không check / không bind máy |
| **E** | **Tình trạng** | **Có** | `Chạy` / `Dừng` / `Out` |
| F | GHI CHÚ | Không | Không đọc |

### Shop chỉ cần

1. **B** = key (vd `Admin`)  
2. **E** = `Chạy`  

Share: **Anyone with the link → Viewer**.

### Cột E

| Giá trị | Ý nghĩa |
|---------|---------|
| **Chạy** | Cho kích hoạt / dùng |
| **Dừng** | Logout key trên máy |
| **Out** | Vô hiệu, xóa session |

## Khách

1. Cài `com.fios.faker` 4.2.6-fios.3 (Sileo `https://vpnhihi.github.io/fios/`)
2. Mở app **Fios**
3. Nhập key → **Kích hoạt**
4. Dùng spoof (engine ChangeInfoIos MG+CT)

Không cần copy ID máy.

## Kỹ thuật

| Thành phần | Path / ghi chú |
|------------|----------------|
| UI + Sheet license | `/var/jb/Applications/Fios.app` (binary iPFaker Sheet B+E) |
| Engine spoof | `/var/jb/usr/lib/TweakInject/ChangeInfoIos{MG,CT}.dylib` |
| Sheet note | `/var/jb/etc/changeinfoios/FIOS_SHEET.txt` |
| Session local | `/var/mobile/Library/iPFaker/license.json` |
| MG gate | Lab-patched UNLICENSED→inert (inject chạy sau sheet OK) |

Env (bridge PC):
```
FIOS_SHEET_ID=1cnfHaeZc1SfDCQZGWI4CDV3vXIT6kGxgCCbVwhPGyno
FIOS_SHEET_GID=0
```
