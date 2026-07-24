#!/usr/bin/env python3
"""
Copy 100% HIOS ChangeInfoIos 4.2.6 → Fios package, rebrand display to Fios,
set activation sheet to user Google Sheet ID.
"""
from __future__ import annotations

import plistlib
import re
import shutil
import struct
from pathlib import Path

ROOT = Path(r"C:\Users\Pem\Desktop\Fios")
HIOS = Path(r"C:\Users\Pem\Desktop\iPFaker\vendor\hios_426")
DEB = Path(r"C:\Users\Pem\Downloads\ChangeInfoIos-v3_4.2.6_iphoneos-arm64.deb")
SHEET_ID = "1cnfHaeZc1SfDCQZGWI4CDV3vXIT6kGxgCCbVwhPGyno"
SHEET_GID = "0"
SHEET_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit?gid={SHEET_GID}#gid={SHEET_GID}"
)
SHEET_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"

# Equal-length binary patches only (safe for Mach-O string tables)
BIN_PATCHES = [
    (b"HIOSFakerV3", b"FiosFakerV3"),  # 11
    (b"HIOS Faker v3", b"Fios Faker v3"),  # 13
    (b"HIOS Faker", b"Fios Faker"),  # 10
    (b"HIOS Faker ", b"Fios Faker "),  # 11 with space variants handled above
]


def copy_tree() -> Path:
    dest = ROOT / "hios_payload"
    if dest.exists():
        shutil.rmtree(dest)
    print("Copying HIOS vendor…", HIOS)
    shutil.copytree(HIOS, dest, ignore=shutil.ignore_patterns("*.pyc", "__pycache__"))
    debs = ROOT / "debs"
    debs.mkdir(exist_ok=True)
    if DEB.is_file():
        shutil.copy2(DEB, debs / DEB.name)
        print("Copied deb", DEB.name)
    # also copy other versions if present
    for p in Path(r"C:\Users\Pem\Downloads").glob("ChangeInfoIos-v3_*.deb"):
        if p.resolve() != DEB.resolve():
            shutil.copy2(p, debs / p.name)
    return dest


def patch_text_file(path: Path) -> None:
    try:
        raw = path.read_bytes()
    except Exception:
        return
    # skip binaries
    if b"\x00" in raw[:200] and path.suffix not in (".plist", ".txt", ".xml", ".json", ".sh"):
        if path.suffix in (".dylib", ".orig") or path.name in ("HIOSFakerV3", "FiosFakerV3"):
            return patch_binary(path)
        if path.suffix == "" and path.stat().st_size > 10000:
            return patch_binary(path)

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("latin-1")
        except Exception:
            return

    orig = text
    repls = [
        ("HIOS Faker v3", "Fios Faker v3"),
        ("HIOS Faker V3", "Fios Faker V3"),
        ("HIOS Faker", "Fios Faker"),
        ("HIOSFakerV3", "FiosFakerV3"),
        ("HIOS / ChangeInfoIos", "Fios / ChangeInfoIos"),
        ("Name: HIOS Faker v3", "Name: Fios Faker v3"),
        ("Maintainer: ChangeInfoIos", "Maintainer: Fios"),
        ("Author: ChangeInfoIos", "Author: Fios"),
        # keep package id com.changeinfoios.v3 for dylib compatibility unless user wants full rename
    ]
    for a, b in repls:
        text = text.replace(a, b)
    if text != orig:
        path.write_text(text, encoding="utf-8", newline="\n")
        print("  text", path.relative_to(ROOT))


def patch_binary(path: Path) -> None:
    data = bytearray(path.read_bytes())
    n = 0
    for old, new in BIN_PATCHES:
        if len(old) != len(new):
            continue
        idx = 0
        while True:
            i = data.find(old, idx)
            if i < 0:
                break
            data[i : i + len(new)] = new
            n += 1
            idx = i + len(new)
    if n:
        path.write_bytes(data)
        print(f"  binary {path.name}: {n} replacements")


def patch_info_plist(app_dir: Path) -> None:
    # binary plist
    info = app_dir / "Info.plist"
    if not info.is_file():
        return
    try:
        d = plistlib.loads(info.read_bytes())
    except Exception as e:
        print("Info.plist parse fail", e)
        return
    d["CFBundleDisplayName"] = "Fios Faker v3"
    d["CFBundleName"] = "FiosFakerV3"
    # keep CFBundleIdentifier com.changeinfoios.v3.app for license/path compatibility
    # or change display only
    if "CFBundleExecutable" in d:
        # executable file rename separate
        pass
    info.write_bytes(plistlib.dumps(d))
    print("  Info.plist display → Fios Faker v3")


def rename_app_bundle(dest: Path) -> None:
    old = dest / "app" / "HIOSFakerV3.app"
    new = dest / "app" / "FiosFakerV3.app"
    if old.is_dir() and not new.exists():
        # rename executable inside first
        exe = old / "HIOSFakerV3"
        if exe.is_file():
            patch_binary(exe)
            exe.rename(old / "FiosFakerV3")
        patch_info_plist(old)
        # update executable name in plist
        info = old / "Info.plist"
        try:
            d = plistlib.loads(info.read_bytes())
            d["CFBundleExecutable"] = "FiosFakerV3"
            d["CFBundleDisplayName"] = "Fios Faker v3"
            d["CFBundleName"] = "FiosFakerV3"
            info.write_bytes(plistlib.dumps(d))
        except Exception:
            pass
        old.rename(new)
        print("  renamed app → FiosFakerV3.app")
    # root tree copy of app
    root_app = dest / "root" / "var" / "jb" / "Applications" / "HIOSFakerV3.app"
    root_new = dest / "root" / "var" / "jb" / "Applications" / "FiosFakerV3.app"
    if root_app.is_dir():
        if root_new.exists():
            shutil.rmtree(root_new)
        # mirror from app/
        if new.is_dir():
            shutil.copytree(new, root_new)
            print("  synced root Applications/FiosFakerV3.app")


def walk_patch(dest: Path) -> None:
    for p in dest.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix in (".dylib", ".orig"):
            # patch string tables in dylibs for display logs only
            patch_binary(p)
            continue
        if p.name in ("HIOSFakerV3", "FiosFakerV3") or (
            p.suffix == "" and "Faker" in p.name and p.stat().st_size > 50000
        ):
            patch_binary(p)
            continue
        if p.suffix.lower() in (
            ".txt",
            ".md",
            ".plist",
            ".json",
            ".sh",
            ".control",
            "",
        ) or p.name in ("control", "postinst", "SOURCE.txt", "MANIFEST.sha256"):
            if p.name == "MANIFEST.sha256":
                continue
            if p.suffix == ".plist" and p.name == "Info.plist":
                continue  # handled
            # binary plists skip text decode
            if p.suffix == ".plist":
                try:
                    raw = p.read_bytes()
                    if raw[:6] == b"bplist":
                        continue
                except Exception:
                    continue
            patch_text_file(p)


def write_branding_and_sheet(dest: Path) -> None:
    (ROOT / "FIOS_SHEET_ACTIVATION.md").write_text(
        f"""# Fios — Kích hoạt license (Google Sheet)

## Trang kích hoạt (Sheet)
{SHEET_URL}

CSV (app/tool đọc):
{SHEET_CSV}

Sheet ID: `{SHEET_ID}`
GID: `{SHEET_GID}`

## Cột (đúng sheet Kích iPFaker)
| Cột | Header | Bắt buộc | Ý nghĩa |
|-----|--------|----------|---------|
| A | STT | Không | Số thứ tự |
| **B** | **Key** | **Có** | Key kích hoạt |
| C | Hạn sử dụng | Không | Optional số ngày; trống = không giới hạn |
| D | ID MÁY | **Không** | **Bỏ** — app không check |
| **E** | **Tình trạng** | **Có** | `Chạy` / `Dừng` / `Out` |
| F | GHI CHÚ | Không | Ghi chú shop |

Shop chỉ cần: **B** = key · **E** = `Chạy`.

Share sheet: **Anyone with the link → Viewer**.

## Ghi chú kỹ thuật
- Payload engine vẫn là ChangeInfoIos dylib (path `/var/jb/etc/changeinfoios`, filter ChangeInfoIosMG/CT) để **không gãy inject**.
- Tên hiển thị app / package = **Fios Faker v3**.
- iPFaker license: chỉ **B + E**; HIOS gốc: `license.plist` + HWID local.

Env (nếu dùng bridge PC):
```
FIOS_SHEET_ID={SHEET_ID}
FIOS_SHEET_GID={SHEET_GID}
```
""",
        encoding="utf-8",
    )

    (ROOT / "fios-brand.json").write_text(
        f"""{{
  "displayName": "Fios",
  "productName": "Fios Faker v3",
  "profile": "fios",
  "sheetId": "{SHEET_ID}",
  "sheetGid": "{SHEET_GID}",
  "sheetUrl": "{SHEET_URL}",
  "sheetCsv": "{SHEET_CSV}",
  "engine": "ChangeInfoIos-4.2.6",
  "source": "HIOS vendor/hios_426 + ChangeInfoIos-v3_4.2.6.deb"
}}
""",
        encoding="utf-8",
    )

    (ROOT / ".env.license").write_text(
        f"FIOS_SHEET_ID={SHEET_ID}\nFIOS_SHEET_GID={SHEET_GID}\n"
        f"HZALO_SHEET_ID={SHEET_ID}\nHZALO_SHEET_GID={SHEET_GID}\n",
        encoding="utf-8",
    )

    (ROOT / "README.md").write_text(
        f"""# Fios

**Fios Faker v3** — rebrand từ **HIOS / ChangeInfoIos 4.2.6** (copy 100% payload).

## Kích hoạt
{SHEET_URL}

Chi tiết cột sheet: [FIOS_SHEET_ACTIVATION.md](FIOS_SHEET_ACTIVATION.md)

## Nội dung
| Path | Mô tả |
|------|--------|
| `hios_payload/` | Full extract HIOS (dylib MG+CT, app, DEBIAN, rootfs) |
| `debs/` | File `.deb` gốc ChangeInfoIos |
| `fios-brand.json` | Brand + sheet |
| `.env.license` | Sheet ID cho tool |

## Cài lên iPhone (rootless)
Dùng Sileo/dpkg với deb trong `debs/`, hoặc đóng gói lại từ `hios_payload/` (app đã đổi tên **Fios Faker v3**).

Engine dylib vẫn tên `ChangeInfoIosMG/CT` (tương thích inject). Chỉ **tên hiển thị / giới thiệu** = Fios.
""",
        encoding="utf-8",
    )

    # control rename Name field
    ctrl = dest / "DEBIAN" / "control"
    if ctrl.is_file():
        t = ctrl.read_text(encoding="utf-8", errors="replace")
        t = t.replace("Name: HIOS Faker v3", "Name: Fios Faker v3")
        t = t.replace("Maintainer: ChangeInfoIos", "Maintainer: Fios")
        t = t.replace("Author: ChangeInfoIos", "Author: Fios")
        # description intro
        t = re.sub(
            r"Description:.*",
            "Description: Fios Faker v3 — device spoof lab (engine ChangeInfoIos 4.2.6). Activation: Google Sheet.",
            t,
            count=1,
        )
        ctrl.write_text(t, encoding="utf-8")
        print("  DEBIAN/control branded")


def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    # clean previous partial asar scan junk optional
    dest = copy_tree()
    print("Patching branding…")
    walk_patch(dest)
    rename_app_bundle(dest)
    write_branding_and_sheet(dest)
    # SOURCE rewrite
    src = dest / "SOURCE.txt"
    src.write_text(
        f"""Fios / ChangeInfoIos import — 100% payload from HIOS
====================================================
Source deb : {DEB}
Sheet activate: {SHEET_URL}
Rebrand    : display Name/UI → Fios Faker v3
Engine     : ChangeInfoIos MG+CT (paths unchanged for inject)

Layout:
  DEBIAN/           control scripts
  dylibs/           ChangeInfoIos MG+CT
  etc/cdhashes
  app/FiosFakerV3.app/
  root/             full data tree
  ar/               original ar members
""",
        encoding="utf-8",
    )
    print("DONE →", ROOT)
    print("Sheet:", SHEET_URL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
