# encoding: utf-8

import os
import time
import subprocess
import lebai_sdk

lebai_sdk.init()
lebai = lebai_sdk.connect("127.0.0.1", True)

SOURCES = {
    "tsinghua": "mirrors.tuna.tsinghua.edu.cn",
    "alibaba": "mirrors.aliyun.com",
    "tencent": "mirrors.cloud.tencent.com",
    "ustc": "mirrors.ustc.edu.cn",
    "sjtu": "mirror.sjtu.edu.cn",
    "ubuntu": "archive.ubuntu.com",
}

def get_ubuntu_codename():
    try:
        with open("/etc/os-release", "r") as f:
            for line in f:
                if line.startswith("UBUNTU_CODENAME="):
                    return line.split("=", 1)[1].strip()
    except Exception:
        pass
    try:
        result = subprocess.run(["lsb_release", "-cs"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None

def get_ubuntu_version():
    try:
        with open("/etc/os-release", "r") as f:
            for line in f:
                if line.startswith("VERSION_ID="):
                    return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return None

def get_cpu_arch():
    try:
        result = subprocess.run(["uname", "-m"], capture_output=True, text=True, timeout=5)
        return result.stdout.strip()
    except Exception:
        return None

def detect_current_source():
    sources_list = "/etc/apt/sources.list"
    try:
        with open(sources_list, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("deb ") and not line.startswith("deb ["):
                    parts = line.split()
                    if len(parts) >= 2:
                        url = parts[1]
                        for name, mirror in SOURCES.items():
                            if mirror in url:
                                return name
                        if "archive.ubuntu.com" in url or "ports.ubuntu.com" in url:
                            return "ubuntu"
    except Exception:
        pass
    return "未知"

def generate_sources_list(mirror_key, codename, arch):
    mirror = SOURCES.get(mirror_key)
    if not mirror:
        return None

    if mirror_key == "ubuntu" and arch == "aarch64":
        mirror = "ports.ubuntu.com"
    suite = "ubuntu-ports" if arch == "aarch64" else "ubuntu"
    components = "main restricted universe multiverse"
    lines = []
    lines.append("deb http://{mirror}/{suite}/ {codename} {components}".format(
        mirror=mirror, suite=suite, codename=codename, components=components))
    lines.append("deb http://{mirror}/{suite}/ {codename}-updates {components}".format(
        mirror=mirror, suite=suite, codename=codename, components=components))
    lines.append("deb http://{mirror}/{suite}/ {codename}-security {components}".format(
        mirror=mirror, suite=suite, codename=codename, components=components))
    lines.append("deb http://{mirror}/{suite}/ {codename}-backports {components}".format(
        mirror=mirror, suite=suite, codename=codename, components=components))
    return "\n".join(lines) + "\n"

def apply_source(mirror_key):
    codename = get_ubuntu_codename()
    arch = get_cpu_arch()
    if not codename:
        lebai.set_item("plugin_ubuntu_sources_status", "失败：无法检测Ubuntu版本")
        return False

    content = generate_sources_list(mirror_key, codename, arch)
    if not content:
        lebai.set_item("plugin_ubuntu_sources_status", "失败：不支持的软件源")
        return False

    try:
        subprocess.run(["sudo", "cp", "/etc/apt/sources.list", "/etc/apt/sources.list.bak"],
                       timeout=10, capture_output=True)
    except Exception:
        pass

    try:
        with open("/tmp/sources.list.new", "w") as f:
            f.write(content)
        subprocess.run(["sudo", "cp", "/tmp/sources.list.new", "/etc/apt/sources.list"],
                       timeout=10, check=True, capture_output=True)
        os.remove("/tmp/sources.list.new")
    except Exception as e:
        lebai.set_item("plugin_ubuntu_sources_status", "失败：写入sources.list出错 - " + str(e))
        return False

    lebai.set_item("plugin_ubuntu_sources_status", "正在执行 apt update...")
    try:
        result = subprocess.run(["sudo", "apt", "update", "-y"],
                                timeout=300, capture_output=True, text=True)
        if result.returncode == 0:
            lebai.set_item("plugin_ubuntu_sources_status", "成功：软件源已切换为" + mirror_key)
            lebai.set_item("plugin_ubuntu_sources_current", mirror_key)
        else:
            lebai.set_item("plugin_ubuntu_sources_status", "失败：apt update出错 - " + result.stderr[:200])
            return False
    except Exception as e:
        lebai.set_item("plugin_ubuntu_sources_status", "失败：apt update超时 - " + str(e))
        return False

    return True

def main():
    arch = get_cpu_arch()
    version = get_ubuntu_version()
    codename = get_ubuntu_codename()

    lebai.set_item("plugin_ubuntu_sources_arch", arch or "未检测到")
    lebai.set_item("plugin_ubuntu_sources_version",
                   ("Ubuntu " + version + " (" + codename + ")") if version and codename else "未检测到")
    lebai.set_item("plugin_ubuntu_sources_current", detect_current_source())
    lebai.set_item("plugin_ubuntu_sources_status", "就绪")

    while True:
        time.sleep(0.5)
        cmd = lebai.get_item("plugin_ubuntu_sources_cmd")['value']
        if cmd and cmd != "":
            if cmd == "apply":
                mirror = lebai.get_item("plugin_ubuntu_sources_mirror")['value']
                if mirror and mirror in SOURCES:
                    apply_source(mirror)
                else:
                    lebai.set_item("plugin_ubuntu_sources_status", "失败：请选择有效的软件源")
            lebai.set_item("plugin_ubuntu_sources_cmd", "")

if __name__ == "__main__":
    main()
