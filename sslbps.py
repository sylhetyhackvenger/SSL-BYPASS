#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Author: SYLHETYHACKVENGER (THE-ERROR808)

Usage: python sslbps.py <app.apk> [output_dir]
Example: python sslbps.py "any.apk"
On Termux: dependencies (apktool, openjdk-17) auto-downloaded on first run.
"""

import os
import re
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request

from colorama import Fore, Back, Style, init
init(autoreset=True)

# =========================
# 🧠 CONFIGURATION
# =========================
SCRIPT_DIR = Path(__file__).resolve().parent
KEYSTORE_PATH = SCRIPT_DIR / "debug.keystore"
KEY_ALIAS = "androiddebugkey"
KEY_PASS = "android"

# Termux: auto-setup URLs
APKTOOL_SCRIPT_URL = "https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool"
APKTOOL_JAR_URL = "https://github.com/iBotPeaches/Apktool/releases/download/v2.9.3/apktool_2.9.3.jar"

# =========================
# 🔥 CINEMATIC BANNER
# =========================
def banner():
    print(Fore.CYAN + Style.BRIGHT + r"""
 .d8888b.   .d8888b.  888                                      
d88P  Y88b d88P  Y88b 888                                      
Y88b.      Y88b.      888                                      
 "Y888b.    "Y888b.   888                                      
    "Y88b.     "Y88b. 888                                      
      "888       "888 888                                      
Y88b  d88P Y88b  d88P 888                                      
 "Y8888P"   "Y8888P"  88888888                                 
                                                               
                                                               
                                                               
888888b. Y88b   d88P 8888888b.     d8888  .d8888b.   .d8888b.  
888  "88b Y88b d88P  888   Y88b   d88888 d88P  Y88b d88P  Y88b 
888  .88P  Y88o88P   888    888  d88P888 Y88b.      Y88b.      
8888888K.   Y888P    888   d88P d88P 888  "Y888b.    "Y888b.   
888  "Y88b   888     8888888P" d88P  888     "Y88b.     "Y88b. 
888    888   888     888      d88P   888       "888       "888 
888   d88P   888     888     d8888888888 Y88b  d88P Y88b  d88P 
8888888P"    888     888    d88P     888  "Y8888P"   "Y8888P"  
                                                               
                                                               
                                                               
""" + Fore.RESET)
    print(Fore.GREEN + Style.BRIGHT + "╔══════════════════════════════════════════════════════════════╗")
    print(Fore.GREEN + "║" + Fore.YELLOW + "      SSL-BYPASS – SSL PINNING + VPN DETECTION REMOVAL     " + Fore.GREEN + "║")
    print(Fore.GREEN + "║" + Fore.CYAN + "      Author: SYLHETYHACKVENGER (THE-ERROR808)                   " + Fore.GREEN + "║")
    print(Fore.GREEN + "║" + Fore.MAGENTA + "      Release: GRAY HAT HACKER Edition | “Break the chains, own the app”" + Fore.GREEN + "║")
    print(Fore.GREEN + "╚══════════════════════════════════════════════════════════════╝" + Fore.RESET)
    print()

# =========================
# ⏳ LOADING EFFECT
# =========================
def loading_animation(text, duration=1.5):
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    end_time = time.time() + duration
    i = 0
    while time.time() < end_time:
        sys.stdout.write(f"\r{Fore.CYAN}[{frames[i % len(frames)]}] {text}{Fore.RESET}   ")
        sys.stdout.flush()
        time.sleep(0.08)
        i += 1
    sys.stdout.write("\r" + " " * (len(text) + 10) + "\r")

# =========================
# 🔧 TERMUX SETUP (unchanged logic)
# =========================
def _is_termux():
    prefix = os.environ.get("PREFIX", "")
    return prefix.startswith("/data/data/com.termux") or prefix == "/data/data/com.termux/files/usr"

def _download(url, dest_path):
    try:
        req = Request(url, headers={"User-Agent": "apk_patcher/1.0"})
        with urlopen(req, timeout=60) as resp:
            data = resp.read()
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(data)
        return True
    except Exception as e:
        print(Fore.RED + f"[!] Download failed: {e}")
        return False

def _termux_setup():
    prefix = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
    bin_dir = Path(prefix) / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    path_env = os.environ.get("PATH", "")
    if str(bin_dir) not in path_env:
        os.environ["PATH"] = str(bin_dir) + os.pathsep + path_env

    if not shutil.which("keytool") and not shutil.which("jarsigner"):
        print(Fore.YELLOW + "[Termux] Java not found. Installing openjdk-17...")
        r = subprocess.run(
            ["pkg", "install", "-y", "openjdk-17"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if r.returncode != 0:
            print(Fore.RED + "pkg install openjdk-17 failed. Run manually: pkg install -y openjdk-17")
            return False
        print(Fore.GREEN + "[Termux] openjdk-17 installed.")
        os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")
    else:
        print(Fore.GREEN + "[Termux] Java OK.")

    if not shutil.which("aapt"):
        print(Fore.YELLOW + "[Termux] aapt not found. Installing aapt...")
        r = subprocess.run(
            ["pkg", "install", "-y", "aapt"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if r.returncode != 0:
            print(Fore.RED + "pkg install aapt failed. Run manually: pkg install -y aapt")
            return False
        print(Fore.GREEN + "[Termux] aapt installed.")
    else:
        print(Fore.GREEN + "[Termux] aapt OK.")

    apktool_cmd = shutil.which("apktool")
    if apktool_cmd:
        print(Fore.GREEN + "[Termux] apktool OK.")
        return True
    apktool_script = bin_dir / "apktool"
    apktool_jar = bin_dir / "apktool.jar"
    if apktool_script.is_file() and apktool_jar.is_file():
        os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")
        print(Fore.GREEN + "[Termux] apktool OK (already in PREFIX/bin).")
        return True
    print(Fore.YELLOW + "[Termux] apktool not found. Downloading...")
    if not _download(APKTOOL_SCRIPT_URL, apktool_script):
        return False
    if not _download(APKTOOL_JAR_URL, apktool_jar):
        return False
    apktool_script.chmod(apktool_script.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")
    print(Fore.GREEN + f"[Termux] apktool installed to {bin_dir}")
    return True

# =========================
# 🧩 SSL PINNING PATCH (unchanged)
# =========================
def _get_manifest_path(decompiled_dir):
    return os.path.join(decompiled_dir, "AndroidManifest.xml")

def _get_res_xml_dir(decompiled_dir):
    return os.path.join(decompiled_dir, "res", "xml")

def _create_network_security_config(decompiled_dir):
    xml_dir = _get_res_xml_dir(decompiled_dir)
    os.makedirs(xml_dir, exist_ok=True)
    path = os.path.join(xml_dir, "network_security_config.xml")
    content = """<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <base-config cleartextTrafficPermitted="true">
        <trust-anchors>
            <certificates src="system" />
            <certificates src="user" />
        </trust-anchors>
    </base-config>
</network-security-config>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path

def _add_network_security_config_to_manifest(decompiled_dir):
    manifest_path = _get_manifest_path(decompiled_dir)
    if not os.path.isfile(manifest_path):
        return False
    with open(manifest_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    if "networkSecurityConfig" in content:
        return True
    application_pattern = re.compile(r"(<application\s+[^>]*)(>)", re.DOTALL)
    replacement = r'\1 android:networkSecurityConfig="@xml/network_security_config"\2'
    new_content, n = application_pattern.subn(replacement, content, count=1)
    if n == 0:
        new_content = content.replace(
            "<application>",
            '<application android:networkSecurityConfig="@xml/network_security_config">',
            1
        )
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    return True

def _apply_ssl_patch(decompiled_dir):
    _create_network_security_config(decompiled_dir)
    _add_network_security_config_to_manifest(decompiled_dir)

# =========================
# 🕵️ VPN PATCH (unchanged)
# =========================
METHOD_BOOL_VPN = re.compile(
    r"(\.method\s+(?:public|private)\s+[^\n]+\)Z\s*\n\s*\.locals\s+\d+\s*\n)(.*?)(\.end method)",
    re.DOTALL
)

def _patch_smali_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception:
        return False
    original = content
    def replacer(m):
        pre, body, suf = m.group(1), m.group(2), m.group(3)
        if "vpn" in body.lower() or "Vpn" in body or "getActiveNetwork" in body or "NetworkCapabilities" in body:
            return pre + "    const/4 v0, 0x0\n    return v0\n" + suf
        return m.group(0)
    content = METHOD_BOOL_VPN.sub(replacer, content)
    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False

def _apply_vpn_patch(decompiled_dir):
    count = 0
    for dirname, _, files in os.walk(decompiled_dir):
        if "smali" not in dirname and "smali_classes" not in dirname:
            continue
        for name in files:
            if not name.endswith(".smali"):
                continue
            path = os.path.join(dirname, name)
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    text = f.read()
            except Exception:
                continue
            if "vpn" not in text.lower() and "Vpn" not in text and "getActiveNetwork" not in text:
                continue
            if _patch_smali_file(path):
                count += 1
    return count

# =========================
# 🔧 APKTOOL & SIGNING (unchanged)
# =========================
def _run(cmd, cwd=None):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            print(Fore.RED + "STDERR:", r.stderr)
            print(Fore.RED + "STDOUT:", r.stdout)
        return r.returncode == 0
    except FileNotFoundError:
        print(Fore.RED + f"Command not found: {cmd[0]}")
        return False
    except subprocess.TimeoutExpired:
        print(Fore.RED + f"Timeout while running: {cmd}")
        return False

def _find_apktool():
    if shutil.which("apktool"):
        return "apktool"
    for name in ["apktool", "apktool.jar"]:
        if shutil.which(name):
            return name
    return "apktool"

def _ensure_keystore():
    if KEYSTORE_PATH.is_file():
        return True
    keytool = shutil.which("keytool")
    if not keytool:
        print(Fore.RED + "keytool not found. Install openjdk-17: pkg install openjdk-17 (Termux) or install JDK on Windows.")
        return False
    cmd = [
        keytool, "-genkey", "-v",
        "-keystore", str(KEYSTORE_PATH), "-alias", KEY_ALIAS,
        "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000",
        "-storepass", KEY_PASS, "-keypass", KEY_PASS,
        "-dname", "CN=Debug, OU=Dev, O=Local, L=City, ST=State, C=US",
    ]
    if not _run(cmd):
        return False
    print(Fore.GREEN + f"Keystore created: {KEYSTORE_PATH}")
    return True

def _sign_apk(apk_path):
    if not _ensure_keystore():
        return False
    jarsigner = shutil.which("jarsigner")
    if not jarsigner:
        print(Fore.RED + "jarsigner not found. Install openjdk-17 (Termux) or JDK on Windows.")
        return False
    return _run([
        jarsigner, "-verbose",
        "-keystore", str(KEYSTORE_PATH), "-storepass", KEY_PASS, "-keypass", KEY_PASS,
        str(apk_path), KEY_ALIAS,
    ])

# =========================
# 📂 PARSE ARGUMENTS (unchanged)
# =========================
def _parse_args():
    if len(sys.argv) < 2:
        return None, None
    args = sys.argv[1:]
    if len(args) >= 3 and os.path.isdir(args[-1]):
        output_dir = Path(args[-1]).resolve()
        apk_path = " ".join(args[:-1])
    elif len(args) >= 2:
        apk_path = args[0]
        if not Path(apk_path).is_file():
            apk_path = " ".join(args)
        output_dir = SCRIPT_DIR / "output"
    else:
        apk_path = args[0]
        output_dir = SCRIPT_DIR / "output"
    return apk_path, output_dir

# =========================
# 🚀 MAIN ENTRY
# =========================
def main():
    banner()
    loading_animation("Initializing neural patching engine", 1.2)

    if len(sys.argv) < 2:
        print(Fore.RED + "[!] Usage: python sslbps.py <app.apk> [output_dir]")
        print(Fore.YELLOW + 'Example: python sslbps.py "any.apk"')
        return 1

    # Termux auto-setup
    if _is_termux():
        print(Fore.CYAN + "[Termux] Checking dependencies...")
        if not _termux_setup():
            print(Fore.RED + "Termux setup failed. Install manually: pkg install -y openjdk-17, then install apktool.")
            return 1

    apk_path_str, out_dir = _parse_args()
    apk_in = Path(apk_path_str).resolve()
    if not apk_in.is_file():
        print(Fore.RED + f"[!] File not found: {apk_in}")
        return 1

    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    decompiled = out_dir / "decompiled"
    if decompiled.exists():
        shutil.rmtree(decompiled)
    apk_out = out_dir / (apk_in.stem + "_patched.apk")
    apktool = _find_apktool()

    print(Fore.CYAN + "\n[1/5] Decompiling APK...")
    if not _run([apktool, "d", str(apk_in), "-o", str(decompiled), "-f"]):
        print(Fore.RED + "Decompile failed. Install apktool (Termux or add to PATH on Windows).")
        return 1

    print(Fore.CYAN + "\n[2/5] Removing SSL Pinning...")
    _apply_ssl_patch(str(decompiled))
    print(Fore.GREEN + "      ✓ Network security config injected.")

    print(Fore.CYAN + "\n[3/5] Removing VPN detection...")
    n = _apply_vpn_patch(str(decompiled))
    print(Fore.GREEN + f"      ✓ Smali files patched: {n}")

    print(Fore.CYAN + "\n[4/5] Rebuilding APK...")
    built = decompiled.parent / (apk_in.stem + "_unsigned.apk")
    build_cmd = [apktool, "b", str(decompiled), "-o", str(built), "-f"]
    if _is_termux():
        build_cmd.insert(2, "--use-aapt1")
    if not _run(build_cmd):
        print(Fore.RED + "Rebuild failed.")
        return 1

    print(Fore.CYAN + "\n[5/5] Signing APK...")
    if not _sign_apk(built):
        print(Fore.RED + f"Signing failed. Unsigned APK at: {built}")
        return 1
    shutil.move(str(built), str(apk_out))
    print(Fore.GREEN + Style.BRIGHT + f"\n✅ Done. Patched APK (SSL pinning + VPN removed, signed): {apk_out}")
    print(Fore.MAGENTA + "╔════════════════════════════════════════════════════════╗")
    print(Fore.MAGENTA + "║  “The wire is yours. No more chains.”                 ║")
    print(Fore.MAGENTA + "║  – SYLHETYHACKVENGER (THE-ERROR808)                   ║")
    print(Fore.MAGENTA + "╚════════════════════════════════════════════════════════╝")
    return 0

if __name__ == "__main__":
    sys.exit(main())
