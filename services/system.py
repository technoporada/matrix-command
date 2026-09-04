"""MatrixCommand - System Info Service"""

import os
import socket
import subprocess
import platform
from typing import Dict, List

import psutil


class SystemInfo:
    def __init__(self):
        self.hostname = socket.gethostname()

    def get_snapshot(self) -> Dict:
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        net = psutil.net_io_counters()

        return {
            "cpu": {
                "percent": cpu,
                "cores": psutil.cpu_count(),
                "freq": self._get_cpu_freq(),
                "load_avg": list(os.getloadavg()) if hasattr(os, "getloadavg") else [],
            },
            "memory": {
                "percent": mem.percent,
                "total_gb": round(mem.total / (1024**3), 2),
                "used_gb": round(mem.used / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
            },
            "disk": {
                "percent": disk.percent,
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
            },
            "network": {
                "sent_mb": round(net.bytes_sent / (1024**2), 2),
                "recv_mb": round(net.bytes_recv / (1024**2), 2),
                "packets_sent": net.packets_sent,
                "packets_recv": net.packets_recv,
            },
            "system": {
                "hostname": self.hostname,
                "os": platform.system(),
                "os_version": platform.release(),
                "python": platform.python_version(),
                "arch": platform.machine(),
                "uptime": self._get_uptime(),
            },
            "connections": self._get_connections(),
            "top_processes": self._get_top_processes(),
        }

    def _get_cpu_freq(self) -> float:
        try:
            freq = psutil.cpu_freq()
            return freq.current if freq else 0
        except Exception:
            return 0

    def _get_uptime(self) -> int:
        try:
            return int(psutil.boot_time())
        except Exception:
            return 0

    def _get_connections(self) -> List[Dict]:
        conns = []
        try:
            for conn in psutil.net_connections(kind="inet")[:50]:
                if conn.status == "ESTABLISHED":
                    conns.append({
                        "local": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "",
                        "remote": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "",
                        "status": conn.status,
                        "pid": conn.pid,
                    })
        except (psutil.AccessDenied, PermissionError):
            pass
        return conns[:30]

    def _get_top_processes(self) -> List[Dict]:
        procs = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                info = proc.info
                if info["cpu_percent"] and info["cpu_percent"] > 0:
                    procs.append({
                        "pid": info["pid"],
                        "name": info["name"][:50],
                        "cpu": round(info["cpu_percent"], 1),
                        "mem": round(info["memory_percent"], 1),
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        procs.sort(key=lambda x: x["cpu"], reverse=True)
        return procs[:15]

    def get_network_interfaces(self) -> List[Dict]:
        interfaces = []
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()

        for name, addr_list in addrs.items():
            iface = {"name": name, "addresses": []}
            for addr in addr_list:
                if addr.family == socket.AF_INET:
                    iface["addresses"].append({"type": "IPv4", "address": addr.address})
                elif addr.family == socket.AF_INET6:
                    iface["addresses"].append({"type": "IPv6", "address": addr.address})

            if name in stats:
                s = stats[name]
                iface["is_up"] = s.isup
                iface["speed"] = s.speed
                iface["mtu"] = s.mtu

            if iface["addresses"]:
                interfaces.append(iface)

        return interfaces
