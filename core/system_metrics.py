"""System metrics via psutil + subprocess."""
import psutil
import subprocess
from datetime import datetime


def _run(cmd: str) -> str:
    try:
        return subprocess.check_output(
            cmd, shell=True, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return ""


def get_cpu() -> dict:
    usage = psutil.cpu_percent(interval=None)
    freq  = psutil.cpu_freq()
    return {
        "usage": usage,
        "usage_str": f"{usage:.0f}%",
        "freq": f"{freq.current:.0f} MHz avg" if freq else "",
        "cores": psutil.cpu_count(logical=True),
    }


def get_memory() -> dict:
    m = psutil.virtual_memory()
    return {
        "used":    f"{m.used  / 1024**3:.1f} GB",
        "total":   f"{m.total / 1024**3:.1f} GB",
        "percent": m.percent,
    }


def get_gpu() -> dict:
    nvidia = _run(
        "nvidia-smi --query-gpu=temperature.gpu,utilization.gpu,name "
        "--format=csv,noheader,nounits 2>/dev/null"
    )
    if nvidia:
        parts = [p.strip() for p in nvidia.split(",")]
        return {"temp": f"{parts[0]}°C", "util": f"{parts[1]}%", "name": parts[2]}

    amd = _run("cat /sys/class/drm/card0/device/hwmon/hwmon*/temp1_input 2>/dev/null")
    if amd:
        t = int(amd) // 1000
        return {"temp": f"{t}°C", "util": "N/A", "name": "AMD GPU"}

    return {"temp": "N/A", "util": "N/A", "name": "Not found"}


def get_uptime() -> dict:
    secs = datetime.now().timestamp() - psutil.boot_time()
    d = int(secs // 86400)
    h = int((secs % 86400) // 3600)
    return {"str": f"{d}d {h}h", "seconds": secs}


def get_network_speed(prev_rx: int, prev_tx: int) -> dict:
    net   = psutil.net_io_counters()
    iface = _run("ip route | grep default | awk '{print $5}' | head -1") or "eth0"
    dl = ul = 0.0
    if prev_rx:
        dl = max(0, (net.bytes_recv - prev_rx) * 8 / 1_000_000)
        ul = max(0, (net.bytes_sent - prev_tx) * 8 / 1_000_000)

    def _fmt(mbit: float) -> str:
        return f"{mbit / 1000:.2f} Gbit/s" if mbit >= 1000 else f"{mbit:.2f} Mbit/s"

    return {
        "iface":    iface,
        "dl_mbit":  dl,
        "ul_mbit":  ul,
        "dl_str":   _fmt(dl),
        "ul_str":   _fmt(ul),
        "rx_bytes": net.bytes_recv,
        "tx_bytes": net.bytes_sent,
        "rx_total": f"{net.bytes_recv / 1024**3:.2f} GB",
        "tx_total": f"{net.bytes_sent / 1024**3:.2f} GB",
    }


def get_disks() -> list[dict]:
    result = []
    skip = ("/boot", "/snap", "/run", "/sys", "/proc", "/dev")
    for p in psutil.disk_partitions():
        if any(p.mountpoint.startswith(s) for s in skip):
            continue
        try:
            u = psutil.disk_usage(p.mountpoint)
            result.append({
                "mount":   p.mountpoint,
                "used":    f"{u.used  / 1024**3:.0f}G",
                "total":   f"{u.total / 1024**3:.0f}G",
                "free":    f"{u.free  / 1024**3:.0f}G",
                "percent": u.percent,
            })
        except PermissionError:
            pass
    return result[:6]


def get_users() -> list[dict]:
    result = []
    for u in psutil.users():
        result.append({
            "name":     u.name,
            "terminal": u.terminal or "pts",
            "started":  datetime.fromtimestamp(u.started).strftime("%Y-%m-%d %H:%M"),
        })
    return result


def get_top_processes(limit: int = 12) -> list[dict]:
    procs = sorted(
        psutil.process_iter(["pid", "username", "name", "cpu_percent", "memory_percent"]),
        key=lambda p: p.info["cpu_percent"] or 0,
        reverse=True,
    )
    result = []
    for p in procs[:limit]:
        i = p.info
        result.append({
            "pid":  str(i["pid"]),
            "user": i["username"] or "",
            "name": i["name"] or "",
            "cpu":  round(i["cpu_percent"] or 0, 1),
            "mem":  round(i["memory_percent"] or 0, 1),
        })
    return result


def get_firewall() -> dict:
    ufw = _run("ufw status 2>/dev/null | head -1")
    if "active" in ufw.lower():
        blocked = int(_run("grep -c 'UFW BLOCK' /var/log/kern.log 2>/dev/null || echo 0") or 0)
        rules   = int(_run("ufw status 2>/dev/null | grep -c 'ALLOW\\|DENY' || echo 0") or 0)
        return {"active": True, "type": "ufw", "blocked": blocked, "rules": rules}
    ipt = _run("iptables -L INPUT 2>/dev/null | wc -l")
    if int(ipt or 0) > 3:
        return {"active": True, "type": "iptables", "blocked": 0, "rules": int(ipt) - 3}
    return {"active": False, "type": "none", "blocked": 0, "rules": 0}