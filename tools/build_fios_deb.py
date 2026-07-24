#!/usr/bin/env python3
"""Build rootless Fios Faker v3 .deb from hios_payload (for Sileo / dpkg)."""
from __future__ import annotations

import hashlib
import io
import tarfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "hios_payload"
DIST = ROOT / "dist"
VERSION = "4.2.6-fios.2"
PKG = "com.fios.faker"


def _norm(name: str) -> str:
    """Debian paths start with ./"""
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


def add_tree(tar: tarfile.TarFile, src: Path, arc_prefix: str) -> None:
    """Add files under src as arc_prefix/..."""
    if not src.is_dir():
        return
    # ensure prefix dir
    parts = arc_prefix.strip("/").split("/")
    acc = ""
    for p in parts:
        acc = f"{acc}{p}/" if acc else f"{p}/"
        # may already exist; tar allows duplicates sometimes — only once
        pass
    add_dir(tar, arc_prefix if arc_prefix.endswith("/") else arc_prefix + "/")
    for f in sorted(src.rglob("*")):
        if not f.is_file():
            continue
        rel = f.relative_to(src).as_posix()
        # parent dirs
        parent = Path(rel).parent
        if str(parent) != ".":
            chain = []
            for part in Path(rel).parent.parts:
                chain.append(part)
                add_dir(tar, arc_prefix.rstrip("/") + "/" + "/".join(chain) + "/")
        mode = 0o755 if (f.suffix == ".dylib" or f.name == "FiosFakerV3" or f.suffix == ".sh") else 0o644
        if f.name == "postinst":
            mode = 0o755
        add_file(tar, f"{arc_prefix.rstrip('/')}/{rel}", f.read_bytes(), mode)


def ar_header(name: str, size: int) -> bytes:
    # GNU ar
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


def control_text() -> str:
    # Replaces com.ipfaker so dpkg/Sileo can overwrite ChangeInfoIos* already owned by iPFaker
    return f"""Package: {PKG}
Name: Fios Faker v3
Version: {VERSION}
Architecture: iphoneos-arm64
Description: Fios Faker v3 device spoof (ChangeInfoIos 4.2.6). Sheet activation.
Homepage: https://docs.google.com/spreadsheets/d/1cnfHaeZc1SfDCQZGWI4CDV3vXIT6kGxgCCbVwhPGyno/edit?gid=0#gid=0
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

mkdir -p "$TI" "$ETC" 2>/dev/null || true

# Prefer TweakInject (Dopamine); mirror to MS if real directory
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

# trust app binary
APP="$ROOT/Applications/FiosFakerV3.app/FiosFakerV3"
if [ -x "$APP" ] && [ -n "$JBCTL" ] && [ -x /var/jb/usr/bin/ldid ]; then
  H=$(/var/jb/usr/bin/ldid -h "$APP" 2>/dev/null | sed -n 's/^CDHash=//p' | head -1)
  [ -n "$H" ] && "$JBCTL" trustcache add "$H" 2>/dev/null || true
fi

for u in uicache /var/jb/usr/bin/uicache; do
  if command -v "$u" >/dev/null 2>&1 || [ -x "$u" ]; then
    "$u" -p "$ROOT/Applications/FiosFakerV3.app" 2>/dev/null || true
    break
  fi
done

echo "Fios Faker v3 installed. Open app Fios Faker v3."
echo "Activation sheet: see /var/jb/etc/changeinfoios/FIOS_SHEET.txt"
exit 0
"""


def build() -> Path:
    if not PAYLOAD.is_dir():
        raise SystemExit(f"missing {PAYLOAD} — run tools/build_fios_from_hios.py first")
    mg = PAYLOAD / "dylibs" / "ChangeInfoIosMG.dylib"
    ct = PAYLOAD / "dylibs" / "ChangeInfoIosCT.dylib"
    pl_mg = PAYLOAD / "dylibs" / "ChangeInfoIosMG.plist"
    pl_ct = PAYLOAD / "dylibs" / "ChangeInfoIosCT.plist"
    app = PAYLOAD / "app" / "FiosFakerV3.app"
    if not (mg.is_file() and ct.is_file() and app.is_dir()):
        raise SystemExit("incomplete payload (dylibs or FiosFakerV3.app)")

    DIST.mkdir(parents=True, exist_ok=True)

    # data.tar.xz like original HIOS deb (Procursus/Sileo happy)
    import lzma

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
            "./var/jb/Applications/FiosFakerV3.app/",
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
            b"Fios activation sheet\n"
            b"https://docs.google.com/spreadsheets/d/1cnfHaeZc1SfDCQZGWI4CDV3vXIT6kGxgCCbVwhPGyno/edit?gid=0#gid=0\n"
            b"CSV: https://docs.google.com/spreadsheets/d/1cnfHaeZc1SfDCQZGWI4CDV3vXIT6kGxgCCbVwhPGyno/export?format=csv&gid=0\n"
        )
        add_file(tar, "./var/jb/etc/changeinfoios/FIOS_SHEET.txt", sheet, 0o644)
        add_file(
            tar,
            "./var/jb/etc/changeinfoios/ENGINE.txt",
            b"Fios Faker v3\nengine=ChangeInfoIos-4.2.6\n",
            0o644,
        )

        for f in sorted(app.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(app).as_posix()
            parent = Path(rel).parent
            if str(parent) != ".":
                chain = []
                for part in parent.parts:
                    chain.append(part)
                    add_dir(tar, "./var/jb/Applications/FiosFakerV3.app/" + "/".join(chain) + "/")
            mode = 0o755 if f.name == "FiosFakerV3" else 0o644
            add_file(tar, f"./var/jb/Applications/FiosFakerV3.app/{rel}", f.read_bytes(), mode)

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
    return out


if __name__ == "__main__":
    build()
