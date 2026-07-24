# Fios Faker v3

Rebrand **HIOS / ChangeInfoIos 4.2.6** + **license Google Sheet** (B Key + E status).

## Cài trên iPhone

### Sileo
```
https://vpnhihi.github.io/fios/
```
Search **Fios** → cài **4.2.6-fios.3**

### Deb trực tiếp
https://github.com/vpnhihi/fios/releases/latest/download/com.fios.faker_4.2.6-fios.3_iphoneos-arm64.deb

1. Tải trên iPhone → Filza / Sileo Open → Install  
2. Mở app **Fios**  
3. Nhập **key** (Sheet cột B) · Sheet cột **E = Chạy** → Kích hoạt  

## Sheet kích hoạt
https://docs.google.com/spreadsheets/d/1cnfHaeZc1SfDCQZGWI4CDV3vXIT6kGxgCCbVwhPGyno/edit?gid=0#gid=0

Chi tiết: [FIOS_SHEET_ACTIVATION.md](FIOS_SHEET_ACTIVATION.md)

| Cột | Bắt buộc |
|-----|----------|
| **B Key** | Có |
| **E Tình trạng** | Có (`Chạy`) |
| C Hạn | Không |
| D ID máy | **Không** (bỏ) |

## Package
- `com.fios.faker` · **4.2.6-fios.3** · iphoneos-arm64 (rootless)
- Engine: ChangeInfoIos MG + CT (HIOS 4.2.6)
- App: **Fios** (Sheet license B+E)
- Replaces: `com.ipfaker` (tránh conflict dylib)

Requires Dopamine / ElleKit, iOS 15+.

## Build (dev)
```bash
python tools/build_fios_deb.py
python tools/publish_sileo.py --all
```
