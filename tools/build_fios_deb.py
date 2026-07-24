#!/usr/bin/env python3
"""Build rootless Fios Faker v3 .deb

4.2.6-fios.3:
  - Engine: ChangeInfoIos MG+CT (HIOS 4.2.6, lab license-gate patched)
  - UI: Fios.app = iPFaker app with Google Sheet license B Key + E status
  - Docs: FIOS_SHEET B+E only (no device bind D)
"""
from __future__ import annotations

import hashlib
import io
import lzma
import plistlib
import shutil
import tarfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "hios_payload"
DIST = ROOT / "dist"
STAGE = ROOT / "build" / "fios_app_stage"
VERSION = "4.2.6-fios.3"
PKG = "com.fios.faker"
SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1cnfHaeZc1SfDCQZGWI4CDV3vXIT6kGxgCCbVwhPGyno/edit?gid=0#gid=0"
)
SHEET_CSV = (
    "https://docs.google.com/spreadsheets/d/"
    "1cnfHaeZc1SfDCQZGWI4CDV3vXIT6kGxgCCbVwhPGyno/export?format=csv&gid=0"
)

# Prefer CI-built iPFaker.app (Sheet B+E license already compiled in)
IPF_APP_CANDIDATES = [
    Path(r"C:\Users\Pem\Desktop\iPFaker\_art_2183\theos\dist\app\iPFaker.app"),
    Path(r"C:\Users\Pem\Desktop\iPFaker\theos\dist\app\iPFaker.app"),
    ROOT.parent / "iPFaker" / "_art_2183" / "theos" / "dist" / "app" / "iPFaker.app",
    ROOT.parent / "iPFaker" / "theos" / "dist" / "app" / "iPFaker.app",
]


def _norm(name: str) -> str:
    if name in (".", "./"):
        return "./"
    if not name.startswith("./"):
        name = "./" + name.lstrip("/")
    return name


def add_dir(tar: tarfile.TarFile, name: str, mode: int = 0o755) -> None:
    name = _norm(name)
    if not name.endswith("/"):
        name += "/"
    info = tarfile.TarInfo(name=name)
    info.type = tarfile.DIRTYPE
    info.mode = mode
    info.mtime = int(time.time())
    info.uid = info.gid = 0
    tar.addfile(info)


def add_file(tar: tarfile.TarFile, name: str, data: bytes, mode: int = 0o644) -> None:
    name = _norm(name)
    info = tarfile.TarInfo(name=name)
    info.size = len(data)
    info.mode = mode
    info.mtime = int(time.time())
    info.uid = info.gid = 0
    tar.addfile(info, io.BytesIO(data))


def ar_header(name: str, size: int) -> bytes:
    n = name.encode("ascii")
    if len(n) > 15:
        n = n[:15]
    return (
        n.ljust(16)
        + str(int(time.time())).encode().ljust(12)
        + b"0".ljust(6)
        + b"0".ljust(6)
        + b"100644".ljust(8)
        + str(size).encode().ljust(10)
        + b"`\n"
    )


def find_ipfaker_app() -> Path:
    for p in IPF_APP_CANDIDATES:
        if p.is_dir() and (p / "iPFaker").is_file():
            return p
    raise SystemExit(
        "missing iPFaker.app with Sheet B+E binary.\n"
        "Need Desktop\\iPFaker\\_art_2183\\theos\\dist\\app\\iPFaker.app "
        "(from CI artifact 2.18.3+)."
    )


def stage_fios_app() -> Path:
    """Copy iPFaker.app → staged Fios.app with Fios branding (binary keeps name iPFaker)."""
    src = find_ipfaker_app()
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True, exist_ok=True)
    dest = STAGE / "Fios.app"
    shutil.copytree(src, dest)

    plist_path = dest / "Info.plist"
    with open(plist_path, "rb") as f:
        pl = plistlib.load(f)
    pl["CFBundleDisplayName"] = "Fios"
    pl["CFBundleName"] = "Fios"
    # Keep executable name matching binary file on disk
    pl["CFBundleExecutable"] = "iPFaker"
    pl["CFBundleIdentifier"] = "com.fios.faker.app"
    pl["CFBundleShortVersionString"] = VERSION
    pl["CFBundleVersion"] = "4263"
    with open(plist_path, "wb") as f:
        plistlib.dump(pl, f)

    # Marker for support / postinst
    (dest / "FIOS_LICENSE.txt").write_text(
        "Fios uses Google Sheet license (same as iPFaker 2.18.3+):\n"
        f"  Sheet: {SHEET_URL}\n"
        "  Required: column B = Key, column E = Chạy\n"
        "  Optional: column C = days (empty = unlimited)\n"
        "  Ignored: column D = ID MÁY (no device bind)\n"
        "Local session: /var/mobile/Library/iPFaker/license.json\n"
        "Engine: ChangeInfoIos MG+CT (HIOS 4.2.6)\n",
        encoding="utf-8",
    )
    print("staged Fios.app from", src)
    return dest


def control_text() -> str:
    return f"""Package: {PKG}
Name: Fios Faker v3
Version: {VERSION}
Architecture: iphoneos-arm64
Description: Fios Faker v3 — HIOS ChangeInfoIos 4.2.6 engine + Sheet license (B Key + E status). No device bind.
Homepage: {SHEET_URL}
Maintainer: Fios
Author: Fios
Section: Tweaks
Depends: firmware (>= 15.0)
Replaces: com.ipfaker, com.changeinfoios.v3, com.changeinfoios.tweak, com.changeinfoios.app, com.changeinfoios
Conflicts: com.changeinfoios.v3, com.changeinfoios.tweak
Provides: com.changeinfoios.v3
"""


def postinst_text() -> str:
    return r"""#!/bin/sh
set -e
ROOT=/var/jb
TI="$ROOT/usr/lib/TweakInject"
MS="$ROOT/Library/MobileSubstrate/DynamicLibraries"
ETC="$ROOT/etc/changeinfoios"
JBCTL=""
for c in "$ROOT/basebin/jbctl" /var/jb/basebin/jbctl; do
  [ -x "$c" ] && JBCTL="$c" && break
done

mkdir -p "$TI" "$ETC" /var/mobile/Library/iPFaker 2>/dev/null || true
chown mobile:mobile /var/mobile/Library/iPFaker 2>/dev/null || true

for n in ChangeInfoIosMG ChangeInfoIosCT; do
  if [ -f "$TI/${n}.dylib" ]; then
    chmod 755 "$TI/${n}.dylib" 2>/dev/null || true
    chown root:wheel "$TI/${n}.dylib" 2>/dev/null || true
  fi
  if [ -f "$TI/${n}.plist" ]; then
    chmod 644 "$TI/${n}.plist" 2>/dev/null || true
    chown root:wheel "$TI/${n}.plist" 2>/dev/null || true
  fi
  if [ -d "$MS" ] && [ ! -L "$MS" ]; then
    [ -f "$TI/${n}.dylib" ] && cp -f "$TI/${n}.dylib" "$MS/${n}.dylib" 2>/dev/null || true
    [ -f "$TI/${n}.plist" ] && cp -f "$TI/${n}.plist" "$MS/${n}.plist" 2>/dev/null || true
  fi
done

if [ -n "$JBCTL" ] && [ -f "$ETC/cdhashes" ]; then
  while IFS= read -r h; do
    [ -z "$h" ] && continue
    "$JBCTL" trustcache add "$h" 2>/dev/null || true
  done < "$ETC/cdhashes"
fi

# Fios UI app (Sheet license binary)
APP_BIN=""
for cand in \
  "$ROOT/Applications/Fios.app/iPFaker" \
  "$ROOT/Applications/FiosFakerV3.app/FiosFakerV3"
do
  if [ -x "$cand" ]; then
    APP_BIN="$cand"
    break
  fi
done
if [ -n "$APP_BIN" ] && [ -n "$JBCTL" ] && [ -x /var/jb/usr/bin/ldid ]; then
  H=$(/var/jb/usr/bin/ldid -h "$APP_BIN" 2>/dev/null | sed -n 's/^CDHash=//p' | head -1)
  [ -n "$H" ] && "$JBCTL" trustcache add "$H" 2>/dev/null || true
fi

for u in uicache /var/jb/usr/bin/uicache; do
  if command -v "$u" >/dev/null 2>&1 || [ -x "$u" ]; then
    [ -d "$ROOT/Applications/Fios.app" ] && "$u" -p "$ROOT/Applications/Fios.app" 2>/dev/null || true
    [ -d "$ROOT/Applications/FiosFakerV3.app" ] && "$u" -p "$ROOT/Applications/FiosFakerV3.app" 2>/dev/null || true
    break
  fi
done

# Remove old HIOS-only home icon if present (prefer Sheet UI app "Fios")
if [ -d "$ROOT/Applications/Fios.app" ] && [ -d "$ROOT/Applications/FiosFakerV3.app" ]; then
  rm -rf "$ROOT/Applications/FiosFakerV3.app" 2>/dev/null || true
  for u in uicache /var/jb/usr/bin/uicache; do
    if command -v "$u" >/dev/null 2>&1 || [ -x "$u" ]; then
      "$u" -a 2>/dev/null || true
      break
    fi
  done
fi

echo "Fios $VERSION installed."
echo "Open app: Fios → nhập Key (Sheet cột B) · cột E = Chạy"
echo "Sheet: see $ETC/FIOS_SHEET.txt"
exit 0
""".replace("$VERSION", VERSION)


def build() -> Path:
    if not PAYLOAD.is_dir():
        raise SystemExit(f"missing {PAYLOAD} — run tools/build_fios_from_hios.py first")
    mg = PAYLOAD / "dylibs" / "ChangeInfoIosMG.dylib"
    ct = PAYLOAD / "dylibs" / "ChangeInfoIosCT.dylib"
    pl_mg = PAYLOAD / "dylibs" / "ChangeInfoIosMG.plist"
    pl_ct = PAYLOAD / "dylibs" / "ChangeInfoIosCT.plist"
    if not (mg.is_file() and ct.is_file()):
        raise SystemExit("incomplete payload dylibs")

    fios_app = stage_fios_app()
    DIST.mkdir(parents=True, exist_ok=True)

    data_buf = io.BytesIO()
    with tarfile.open(fileobj=data_buf, mode="w") as tar:
        add_dir(tar, "./")
        for d in [
            "./var/",
            "./var/jb/",
            "./var/jb/usr/",
            "./var/jb/usr/lib/",
            "./var/jb/usr/lib/TweakInject/",
            "./var/jb/etc/",
            "./var/jb/etc/changeinfoios/",
            "./var/jb/Applications/",
            "./var/jb/Applications/Fios.app/",
            "./var/mobile/",
            "./var/mobile/Library/",
            "./var/mobile/Library/iPFaker/",
        ]:
            add_dir(tar, d)

        ti = "./var/jb/usr/lib/TweakInject"
        add_file(tar, f"{ti}/ChangeInfoIosMG.dylib", mg.read_bytes(), 0o755)
        add_file(tar, f"{ti}/ChangeInfoIosCT.dylib", ct.read_bytes(), 0o755)
        add_file(tar, f"{ti}/ChangeInfoIosMG.plist", pl_mg.read_bytes(), 0o644)
        add_file(tar, f"{ti}/ChangeInfoIosCT.plist", pl_ct.read_bytes(), 0o644)

        cd = PAYLOAD / "etc" / "cdhashes"
        if cd.is_file():
            add_file(tar, "./var/jb/etc/changeinfoios/cdhashes", cd.read_bytes(), 0o644)

        sheet = (
            "Fios activation - Google Sheet (same as iPFaker)\n"
            f"{SHEET_URL}\nCSV: {SHEET_CSV}\n\n"
            "Required columns:\n"
            "  B = Key\n"
            "  E = Status: Chay / Dung / Out\n"
            "Optional:\n"
            "  C = Days; empty = unlimited\n"
            "Ignored:\n"
            "  D = Device ID (no bind)\n"
            "\nOpen app Fios -> enter key -> Activate.\n"
            "Local: /var/mobile/Library/iPFaker/license.json\n"
            "Engine: ChangeInfoIos MG+CT (HIOS 4.2.6, lab gate patched)\n"
        ).encode("utf-8")
        add_file(tar, "./var/jb/etc/changeinfoios/FIOS_SHEET.txt", sheet, 0o644)
        add_file(
            tar,
            "./var/jb/etc/changeinfoios/ENGINE.txt",
            f"Fios Faker v3\nversion={VERSION}\nengine=ChangeInfoIos-4.2.6\n"
            f"license=sheet-B-E\nui=Fios.app(iPFaker-sheet)\n".encode(),
            0o644,
        )
        add_file(
            tar,
            "./var/mobile/Library/iPFaker/README_FIOS.txt",
            b"Fios stores sheet session here (shared layout with iPFaker license code).\n",
            0o644,
        )

        for f in sorted(fios_app.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(fios_app).as_posix()
            parent = Path(rel).parent
            if str(parent) != ".":
                chain = []
                for part in parent.parts:
                    chain.append(part)
                    add_dir(tar, "./var/jb/Applications/Fios.app/" + "/".join(chain) + "/")
            mode = 0o755 if f.name == "iPFaker" else 0o644
            add_file(tar, f"./var/jb/Applications/Fios.app/{rel}", f.read_bytes(), mode)

    raw_tar = data_buf.getvalue()
    data = lzma.compress(raw_tar)

    ctrl_buf = io.BytesIO()
    with tarfile.open(fileobj=ctrl_buf, mode="w") as tar:
        add_dir(tar, "./")
        add_file(tar, "./control", control_text().encode(), 0o644)
        add_file(tar, "./postinst", postinst_text().encode(), 0o755)
    ctrl = lzma.compress(ctrl_buf.getvalue())

    deb_name = f"{PKG}_{VERSION}_iphoneos-arm64.deb"
    out = DIST / deb_name
    with open(out, "wb") as f:
        f.write(b"!<arch>\n")
        for name, blob in (
            ("debian-binary", b"2.0\n"),
            ("control.tar.xz", ctrl),
            ("data.tar.xz", data),
        ):
            f.write(ar_header(name, len(blob)))
            f.write(blob)
            if len(blob) % 2 == 1:
                f.write(b"\n")

    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    (DIST / f"{deb_name}.sha256").write_text(f"{sha}  {deb_name}\n", encoding="utf-8")
    print("wrote", out, "size", out.stat().st_size)
    print("sha256", sha)
    print("license: Sheet B=Key E=status (iPFaker binary in Fios.app)")
    return out


if __name__ == "__main__":
    build()
