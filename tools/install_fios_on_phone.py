#!/usr/bin/env python3
import paramiko
from pathlib import Path

HOST, USER, PASS = "192.168.1.12", "mobile", "alpine"
ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / "dist" / "com.fios.faker_4.2.6-fios.2_iphoneos-arm64.deb"


def main() -> int:
    if not LOCAL.is_file():
        print("missing", LOCAL)
        return 2
    print("local", LOCAL.stat().st_size)
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=PASS, timeout=15, allow_agent=False, look_for_keys=False)
    sftp = c.open_sftp()
    remote = "/var/mobile/Documents/fios_v2.deb"
    sftp.put(str(LOCAL), remote)
    script = """#!/bin/sh
export PATH=/var/jb/usr/bin:/var/jb/bin:/usr/bin:/bin:$PATH
dpkg -r com.fios.faker 2>/dev/null || true
dpkg -i /var/mobile/Documents/fios_v2.deb 2>&1
echo EXIT:$?
echo --- app ---
ls -la /var/jb/Applications/FiosFakerV3.app/ 2>&1 | head -12
echo --- dylibs ---
ls -la /var/jb/usr/lib/TweakInject/ChangeInfoIosMG.dylib /var/jb/usr/lib/TweakInject/ChangeInfoIosCT.dylib 2>&1
echo --- dpkg ---
dpkg -l | grep -i fios
dpkg -l | grep -i ipfaker | head -5
"""
    with sftp.file("/var/mobile/Documents/_fi.sh", "w") as f:
        f.write(script)
    sftp.chmod("/var/mobile/Documents/_fi.sh", 0o755)
    sftp.close()
    _, o, e = c.exec_command(
        f"echo {PASS} | sudo -S -p '' sh /var/mobile/Documents/_fi.sh", timeout=120
    )
    print((o.read() + e.read()).decode(errors="replace"))
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
