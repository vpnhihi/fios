#!/usr/bin/env python3
"""Stage docs/ Sileo repo from latest dist deb and optionally push gh-pages + release."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
DOCS = ROOT / "docs"
VERSION = "4.2.6-fios.3"
PKG = "com.fios.faker"
DEB_NAME = f"{PKG}_{VERSION}_iphoneos-arm64.deb"
SHEET = (
    "https://docs.google.com/spreadsheets/d/"
    "1cnfHaeZc1SfDCQZGWI4CDV3vXIT6kGxgCCbVwhPGyno/edit?gid=0#gid=0"
)


def stage() -> Path:
    src = DIST / DEB_NAME
    if not src.is_file():
        raise SystemExit(f"missing {src} — run tools/build_fios_deb.py first")
    debs = DOCS / "debs"
    debs.mkdir(parents=True, exist_ok=True)
    for p in debs.glob("com.fios.faker_*.deb"):
        p.unlink()
    shutil.copy2(src, debs / src.name)
    data = src.read_bytes()
    size = len(data)
    md5 = hashlib.md5(data).hexdigest()
    sha1 = hashlib.sha1(data).hexdigest()
    sha256 = hashlib.sha256(data).hexdigest()
    pkg = f"""Package: {PKG}
Name: Fios Faker v3
Version: {VERSION}
Architecture: iphoneos-arm64
Maintainer: Fios
Author: Fios
Section: Tweaks
Depends: firmware (>= 15.0)
Replaces: com.ipfaker, com.changeinfoios.v3, com.changeinfoios.tweak, com.changeinfoios.app
Filename: debs/{src.name}
Size: {size}
MD5sum: {md5}
SHA1: {sha1}
SHA256: {sha256}
Description: Fios Faker v3. HIOS 4.2.6 engine + Sheet license B=Key E=Chay (no device bind).
Homepage: https://github.com/vpnhihi/fios
Depiction: https://vpnhihi.github.io/fios/

"""
    (DOCS / "Packages").write_bytes(pkg.encode("utf-8"))
    with gzip.open(DOCS / "Packages.gz", "wb") as gz:
        gz.write(pkg.encode("utf-8"))
    (DOCS / "Release").write_text(
        "Origin: Fios\nLabel: Fios\nSuite: stable\nVersion: 1.0\nCodename: ios\n"
        "Architectures: iphoneos-arm64\nComponents: main\nDescription: Fios repo\n",
        encoding="utf-8",
        newline="\n",
    )
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    (DOCS / "sileo-source.txt").write_text(
        "https://vpnhihi.github.io/fios/\n", encoding="utf-8"
    )
    (DOCS / "index.html").write_text(
        f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fios Sileo</title>
<style>
body{{font-family:-apple-system,sans-serif;background:#0b0f14;color:#e8eef5;padding:20px;max-width:560px;margin:auto;line-height:1.5}}
pre{{background:#151b24;padding:12px;border-radius:10px;word-break:break-all}}
.btn{{display:block;background:#0d9488;color:#fff;text-align:center;padding:14px;border-radius:12px;text-decoration:none;font-weight:700;margin:12px 0}}
.box{{background:#151b24;padding:12px;border-radius:10px;margin:12px 0}}
a{{color:#5eead4}}
</style></head><body>
<h1>Fios Repo</h1>
<p><b>Sileo → Sources → + → dán:</b></p>
<pre>https://vpnhihi.github.io/fios/</pre>
<p>Refresh → search <b>Fios</b> → cài <b>{VERSION}</b></p>
<a class="btn" href="debs/{DEB_NAME}">Tải deb {VERSION}</a>
<div class="box">
<strong>{VERSION}</strong><br>
· Engine ChangeInfoIos 4.2.6 (HIOS)<br>
· App <b>Fios</b> — license Google Sheet<br>
· Cột <b>B = Key</b> · <b>E = Chạy</b> (không cần cột D ID máy)
</div>
<p>Sheet: <a href="{SHEET}">mở Google Sheet</a></p>
</body></html>
""",
        encoding="utf-8",
    )
    print("staged", src.name, size)
    print(pkg)
    return src


def push_gh_pages() -> None:
    stage()
    user, password = "vpnhihi", ""
    p = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        text=True,
        capture_output=True,
        check=True,
    )
    for line in p.stdout.splitlines():
        if line.startswith("username="):
            user = line.split("=", 1)[1]
        if line.startswith("password="):
            password = line.split("=", 1)[1]
    if not password:
        raise SystemExit("no git credentials for github.com")

    tmp = Path(tempfile.mkdtemp(prefix="fios-pages-"))
    for item in DOCS.iterdir():
        dest = tmp / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)
    (tmp / ".nojekyll").write_text("", encoding="utf-8")

    def run(cmd: list[str], env=None) -> None:
        print("+", " ".join(cmd))
        subprocess.check_call(cmd, cwd=tmp, env=env)

    run(["git", "init", "-b", "gh-pages"])
    run(["git", "config", "user.email", "fios-lab@local"])
    run(["git", "config", "user.name", "Fios Lab"])
    run(["git", "add", "-A"])
    run(["git", "commit", "-m", f"fios sileo {VERSION}"])
    ask = tmp / "askpass.py"
    ask.write_text(
        "#!/usr/bin/env python3\nimport os\nprint(os.environ.get('GIT_PASSWORD',''))\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["GIT_PASSWORD"] = password
    env["GIT_ASKPASS"] = str(ask)
    env["GIT_TERMINAL_PROMPT"] = "0"
    subprocess.check_call(
        [
            "git",
            "push",
            "-f",
            f"https://{user}@github.com/vpnhihi/fios.git",
            "HEAD:gh-pages",
        ],
        cwd=tmp,
        env=env,
    )
    print("OK gh-pages → https://vpnhihi.github.io/fios/")


def release() -> None:
    src = DIST / DEB_NAME
    if not src.is_file():
        raise SystemExit(f"missing {src}")
    sha = DIST / f"{DEB_NAME}.sha256"
    tag = f"v{VERSION}"
    # delete existing tag/release if present
    subprocess.run(["gh", "release", "delete", tag, "-y"], cwd=ROOT)
    subprocess.run(["git", "tag", "-d", tag], cwd=ROOT)
    subprocess.run(["git", "push", "origin", f":refs/tags/{tag}"], cwd=ROOT)
    notes = f"""Fios Faker v3 **{VERSION}**

- Engine: ChangeInfoIos MG+CT (HIOS 4.2.6)
- App **Fios**: Google Sheet license (B=Key, E=Chạy) — no device bind (D ignored)
- Sileo: https://vpnhihi.github.io/fios/
- Sheet: {SHEET}
"""
    cmd = [
        "gh",
        "release",
        "create",
        tag,
        str(src),
        str(sha) if sha.is_file() else "",
        "--title",
        f"Fios Faker v3 {VERSION}",
        "--notes",
        notes,
    ]
    cmd = [c for c in cmd if c]
    print("+", " ".join(cmd[:6]), "...")
    subprocess.check_call(cmd, cwd=ROOT)
    print("OK release", tag)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage-only", action="store_true")
    ap.add_argument("--push-pages", action="store_true")
    ap.add_argument("--release", action="store_true")
    ap.add_argument("--all", action="store_true", help="stage + pages + release")
    args = ap.parse_args()
    if args.all:
        stage()
        push_gh_pages()
        release()
        return 0
    if args.push_pages:
        push_gh_pages()
        return 0
    if args.release:
        stage()
        release()
        return 0
    stage()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
