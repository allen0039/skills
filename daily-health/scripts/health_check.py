#!/usr/bin/env python3
"""
Daily Health Check - 系统健康检查脚本
纯只读检查，不会修改任何配置
"""
import subprocess
import re
import os
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# ── 端口→服务映射（根据你的实际服务修改）──────────────────────
PORT_SERVICE_MAP = {
    22: "SSH",
    53: "DNS (systemd-resolved)",
    80: "HTTP",
    443: "HTTPS",
    111: "RPCBind",
}

# ── 需要公网暴露检查的敏感端口 ────────────────────────────
SENSITIVE_PORTS = {22, 111, 80, 443, 3306, 5432, 6379, 27017, 8080, 9200}


def run_cmd(cmd: str, timeout: int = 30) -> Tuple[bool, str]:
    """执行命令，返回 (成功, 输出)"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "命令超时"
    except Exception as e:
        return False, str(e)


def check_system_info() -> Dict:
    """检查系统基本信息"""
    info = {"status": "✅", "items": []}

    # 系统版本
    ok, output = run_cmd("cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d'\"' -f2")
    if ok and output:
        info["items"].append(("系统", output))

    # 内核
    ok, output = run_cmd("uname -sr")
    if ok:
        _, arch = run_cmd("uname -m")
        info["items"].append(("内核", f"{output} ({arch})"))

    # 运行时间（转为中文格式）
    ok, output = run_cmd("uptime -p")
    if ok:
        uptime_str = output.replace("up ", "").strip()
        total_days = 0
        weeks = re.search(r'(\d+)\s*week', uptime_str)
        days = re.search(r'(\d+)\s*day', uptime_str)
        hours = re.search(r'(\d+)\s*hour', uptime_str)
        if weeks:
            total_days += int(weeks.group(1)) * 7
        if days:
            total_days += int(days.group(1))
        hours_str = ""
        if hours:
            hours_str = f" {hours.group(1)} 小时"
        if total_days > 0:
            info["items"].append(("运行时间", f"{total_days} 天{hours_str}"))

    # 系统负载
    ok, output = run_cmd("cat /proc/loadavg")
    if ok:
        parts = output.split()
        if len(parts) >= 3:
            info["items"].append(("负载", f"{parts[0]} / {parts[1]} / {parts[2]}"))

    # CPU 核数
    ok, output = run_cmd("nproc")
    if ok:
        info["items"].append(("CPU 核数", output))

    # 磁盘使用
    ok, output = run_cmd("df -h / | awk 'NR==2 {printf \"%s / %s (%s)\", $3, $2, $5}'")
    if ok:
        pct_match = re.search(r'\((\d+)%\)', output)
        pct = int(pct_match.group(1)) if pct_match else 0
        flag = " ⚠️" if pct > 80 else ""
        info["items"].append(("磁盘", f"{output}{flag}"))

    # 内存使用
    ok, output = run_cmd(
        "free -h | awk '/^Mem:/ {avail=$7; total=$2; used=$3; printf \"%s / %s (可用 %s)\", used, total, avail}'"
    )
    if ok:
        info["items"].append(("内存", output))

    # Swap
    ok, output = run_cmd("free -h | awk '/^Swap:/ {printf \"%s / %s\", $3, $2}'")
    if ok and output and "0B" not in output.split("/")[0].strip():
        info["items"].append(("Swap", output))
    elif ok:
        info["items"].append(("Swap", f"{output} (几乎未使用)"))

    return info


def check_listening_ports() -> Dict:
    """检查监听端口，格式化为简洁表格"""
    info = {"status": "✅", "items": []}

    ok, output = run_cmd(
        "ss -tlnp 2>/dev/null | awk 'NR>1 {print $4, $6}' | grep -v '^$'"
    )
    if ok and output:
        seen_ports = set()
        port_services = []
        public_ports = []
        loopback_count = 0
        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) < 1:
                continue

            addr = parts[0]

            # 提取端口号
            port = None
            port_match = re.search(r':(\d+)$', addr)
            if port_match:
                port = int(port_match.group(1))

            # 判断是否 loopback
            is_loopback = addr.startswith("127.") or addr.startswith("[::1]") or "127.0.0.53" in addr or "127.0.0.54" in addr

            # 获取服务名
            service = PORT_SERVICE_MAP.get(port, "")
            if not service:
                lower = line.lower()
                if "openresty" in lower or "nginx" in lower:
                    service = "Nginx/OpenResty"
                elif "node" in lower:
                    service = "Node.js"
                elif "python3" in line:
                    service = "Python3"
                elif "docker" in lower:
                    service = "Docker 容器"
                else:
                    service = "unknown"

            if is_loopback:
                location = "loopback"
                loopback_count += 1
            else:
                location = "公网"

            key = port or 0
            if key not in seen_ports:
                seen_ports.add(key)
                port_services.append((key, service, location))
            if not is_loopback and port and port in SENSITIVE_PORTS:
                public_ports.append(port)

        port_services.sort(key=lambda x: x[0])

        total = len(port_services)
        info["items"].append(("监听端口总数", f"{total} 个 (其中 {loopback_count} 个仅本地)"))

        if public_ports:
            port_names = [PORT_SERVICE_MAP.get(p, str(p)) for p in public_ports]
            info["public_exposure"] = public_ports
            info["public_names"] = port_names

    if not info["items"]:
        info["items"].append(("无", "未发现监听端口"))

    return info


def check_docker() -> Dict:
    """检查 Docker 容器状态"""
    info = {"status": "✅", "items": []}

    ok, output = run_cmd("docker ps --format '{{.Names}}\t{{.Status}}' 2>/dev/null")
    if ok and output:
        lines = [l.strip() for l in output.strip().split("\n") if l.strip()]
        if lines:
            info["items"].append(("容器总数", f"{len(lines)} 个"))
            for line in lines:
                parts = line.split("\t")
                if len(parts) >= 2:
                    name = parts[0].strip()
                    status = parts[1].strip()
                    flag = "✅" if "Up" in status else "❌"
                    if "healthy" in status.lower():
                        status_short = "healthy"
                    elif "unhealthy" in status.lower():
                        status_short = "unhealthy"
                    else:
                        status_short = "running" if "Up" in status else "stopped"
                    info["items"].append((name, f"{flag} {status_short}"))
        else:
            info["items"].append(("Docker", "无运行中的容器"))
    else:
        info["status"] = "⚠️"
        info["items"].append(("Docker", "⚠️ 无法访问或未安装"))

    return info


def check_security() -> Dict:
    """安全审计检查"""
    info = {"status": "✅", "items": []}

    # SSH 端口
    ok, output = run_cmd("ss -tlnp | grep sshd | awk '{print $4}' | grep -oP ':\\K\\d+' | head -1")
    ssh_port = output if ok and output else "22"
    is_standard = ssh_port == "22"
    if is_standard:
        info["items"].append(("SSH 端口", f"{ssh_port} ⚠️ 标准端口"))
    else:
        info["items"].append(("SSH 端口", f"{ssh_port} ✅ 非标准端口"))

    # PermitRootLogin 配置
    ok, output = run_cmd("grep -i 'PermitRootLogin' /etc/ssh/sshd_config 2>/dev/null | grep -v '^#' | head -1")
    if ok and output:
        value = output.split()[-1] if output.split() else "unknown"
        if value.lower() == "yes":
            info["status"] = "⚠️"
            info["items"].append(("PermitRootLogin", f"⚠️ {value} (建议改为 prohibit-password)"))
        elif value.lower() in ("without-password", "prohibit-password"):
            info["items"].append(("PermitRootLogin", f"✅ {value}"))
        else:
            info["items"].append(("PermitRootLogin", f"{value}"))
    else:
        info["items"].append(("PermitRootLogin", "未明确配置 (默认)"))

    # SSH 暴力破解 (24h)
    ok, output = run_cmd(
        "journalctl -u ssh --since '24 hours ago' 2>/dev/null | grep -ci 'failed\\|invalid' || echo 0"
    )
    if ok:
        try:
            count = int(output)
        except ValueError:
            count = 0
        if count > 100:
            info["status"] = "⚠️"
            info["items"].append(("暴力破解 (24h)", f"⚠️ {count} 次 (频繁攻击)"))
        elif count > 10:
            info["status"] = "⚠️"
            info["items"].append(("暴力破解 (24h)", f"⚠️ {count} 次"))
        else:
            info["items"].append(("暴力破解 (24h)", f"{count} 次"))

    # 防火墙状态
    ok, output = run_cmd("ufw status 2>/dev/null")
    if ok:
        if "active" in output.lower():
            info["items"].append(("防火墙", "✅ ufw 已激活"))
        else:
            info["status"] = "⚠️"
            info["items"].append(("防火墙", "⚠️ ufw 未激活"))
    else:
        ok2, output2 = run_cmd("iptables -L -n 2>/dev/null | head -3")
        if ok2 and ("DROP" in output2 or "REJECT" in output2):
            info["items"].append(("防火墙", "✅ iptables 有规则"))
        else:
            info["items"].append(("防火墙", "⚠️ 未检测到有效防火墙规则"))

    # fail2ban 状态
    ok, output = run_cmd("systemctl is-active fail2ban 2>/dev/null")
    if ok and output == "active":
        ok2, banned = run_cmd("fail2ban-client status sshd 2>/dev/null | grep 'Total banned' | awk '{print $NF}'")
        ban_count = banned if ok2 and banned.strip().isdigit() else "?"
        info["items"].append(("fail2ban", f"✅ 运行中 (已封禁 {ban_count} 个 IP)"))
    else:
        info["items"].append(("fail2ban", "⚠️ 未安装或未运行"))

    # 公网暴露端口
    ok, output = run_cmd("ss -tlnp | awk 'NR>1 {print $4}' | grep -v '127\\.\\|\\[::1\\]\\|127\\.0\\.0\\.' | grep -oP ':\\K\\d+' | sort -un")
    if ok and output:
        exposed = [int(p) for p in output.split("\n") if p.strip().isdigit()]
        sensitive_exposed = [p for p in exposed if p in SENSITIVE_PORTS]
        if sensitive_exposed:
            names = [PORT_SERVICE_MAP.get(p, str(p)) for p in sensitive_exposed]
            info["items"].append(("公网暴露端口", f"{', '.join(names)} 对公网开放"))

    return info


def check_updates() -> Dict:
    """检查系统更新"""
    info = {"status": "✅", "items": []}

    ok, output = run_cmd("apt list --upgradable 2>/dev/null | grep -v '^Listing'")
    if ok and output:
        lines = [l.strip() for l in output.split("\n") if l.strip()]
        count = len(lines)
        if count > 0:
            ok2, sec_output = run_cmd("apt list --upgradable 2>/dev/null | grep -i security | wc -l")
            sec_count = int(sec_output) if ok2 and sec_output.strip().isdigit() else 0

            if count > 20:
                info["status"] = "⚠️"
            info["items"].append(("待更新包", f"{count} 个 (安全更新: {sec_count} 个)"))
        else:
            info["items"].append(("待更新包", "系统已是最新 ✅"))
    else:
        info["items"].append(("待更新包", "系统已是最新 ✅"))

    return info


def generate_report(checks: Dict) -> str:
    """生成报告 — 标准 Markdown 格式"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    def cv(text):
        """把值包裹在反引号中"""
        return f"`{str(text)}`"

    report = f"🖥️ *每日系统健康检查 — {now}*\n\n"

    # 📋 系统信息
    sys_info = checks["系统信息"]
    report += "📋 *系统信息*\n"
    for label, value in sys_info["items"]:
        report += f"• `{label}`: {cv(value)}\n"
    report += "\n"

    # 🌐 监听端口
    ports = checks["监听端口"]
    report += "🌐 *监听端口*\n"
    for label, value in ports["items"]:
        report += f"• {cv(value)}\n"
    report += "\n"

    # 🐳 容器服务
    docker = checks["Docker"]
    report += "🐳 *容器服务*\n"
    for label, value in docker["items"]:
        report += f"• `{label}`: {cv(value)}\n"
    report += "\n"

    # 🔒 安全审计
    sec = checks["安全审计"]
    report += "🔒 *安全审计*\n"
    for label, value in sec["items"]:
        report += f"• `{label}`: {cv(value)}\n"
    report += "\n"

    # 📦 更新状态
    upd = checks["更新状态"]
    report += "📦 *更新状态*\n"
    for label, value in upd["items"]:
        report += f"• `{label}`: {cv(value)}\n"
    report += "\n"

    # ⚠️ 建议
    suggestions = []
    if checks["安全审计"]["status"] != "✅":
        for label, value in checks["安全审计"]["items"]:
            if "⚠️" in str(value):
                if "PermitRootLogin" in label:
                    suggestions.append("SSH PermitRootLogin=yes → 建议改为 prohibit-password 或 no")
                elif "防火墙" in label:
                    suggestions.append("建议启用 ufw 防火墙，仅放行需要的端口")
                elif "暴力破解" in label:
                    has_f2b = any("fail2ban" in l and "✅" in str(val) for l, val in checks["安全审计"]["items"])
                    if not has_f2b:
                        suggestions.append("考虑安装 fail2ban 防止暴力破解")

    disk_item = next((val for l, val in checks["系统信息"]["items"] if l == "磁盘"), "")
    if "⚠️" in disk_item:
        pct = re.search(r'\((\d+)%\)', disk_item)
        if pct and int(pct.group(1)) > 80:
            suggestions.append(f"磁盘使用 {pct.group(1)}%，建议清理或扩容")

    if suggestions:
        report += "⚠️ *建议*\n"
        for s in suggestions:
            report += f"• `{s}`\n"
    else:
        report += "✅ *一切正常，无需操作*\n"

    return report


def main():
    """主函数"""
    checks = {
        "系统信息": check_system_info(),
        "监听端口": check_listening_ports(),
        "Docker": check_docker(),
        "安全审计": check_security(),
        "更新状态": check_updates(),
    }

    report = generate_report(checks)
    print(report)


if __name__ == "__main__":
    main()
