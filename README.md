# 🩺 Daily Health Check

一个轻量级的 Linux 系统健康检查工具，可配合 Hermes Agent 定时执行，也可独立使用。

## 功能

- 📋 **系统信息** — 版本、内核、运行时间、负载、CPU、磁盘、内存、Swap
- 🌐 **监听端口** — 端口→服务映射，loopback/公网标识
- 🐳 **Docker 容器** — 容器状态、健康检查
- 🔒 **安全审计** — SSH 配置、暴力破解检测、防火墙、fail2ban
- 📦 **更新状态** — 待更新包数量、安全更新分类
- ⚠️ **智能建议** — 根据检查结果自动生成可操作的优化建议

## 快速开始

### 独立使用

```bash
# 直接运行
python3 scripts/health_check.py

# 或设置可执行权限后运行
chmod +x scripts/health_check.py
./scripts/health_check.py
```

### 配合 Hermes Agent

1. 将 `daily-health` 目录放到 `~/.hermes/skills/<category>/` 下
2. 复制脚本到 Hermes scripts 目录：
   ```bash
   cp scripts/health_check.py ~/.hermes/scripts/health_check.py
   ```
3. 在 Hermes Agent 中创建 cron job：
   ```
   /cron create
   - schedule: 0 8 * * *
   - script: health_check.py
   - deliver: telegram
   - no_agent: true
   ```

## 自定义

### 端口映射

编辑 `scripts/health_check.py` 中的 `PORT_SERVICE_MAP`，添加你的服务：

```python
PORT_SERVICE_MAP = {
    22: "SSH",
    80: "HTTP",
    443: "HTTPS",
    8080: "我的 Web 服务",
    3000: "Node.js 应用",
}
```

### 敏感端口

`SENSITIVE_PORTS` 集合定义了需要检查公网暴露的端口，按需添加：

```python
SENSITIVE_PORTS = {22, 80, 443, 3306, 5432, 6379, 27017, 8080, 9200}
```

## 输出示例

```
🖥️ *每日系统健康检查 — 2026-06-11 08:00*

📋 *系统信息*
• `系统`: `Ubuntu 22.04.3 LTS`
• `内核`: `Linux 5.15.0-91-generic (x86_64)`
• `运行时间`: `45 天 3 小时`
• `负载`: `0.15 / 0.10 / 0.08`
• `CPU 核数`: `4`
• `磁盘`: `12G / 40G (30%)`
• `内存`: `2.1G / 8G (可用 5.2G)`
• `Swap`: `0B / 2G (几乎未使用)`

🌐 *监听端口*
• `8 个 (其中 3 个仅本地)`

🐳 *容器服务*
• `容器总数`: `3 个`
• `nginx`: `✅ running`
• `redis`: `✅ running`
• `myapp`: `✅ healthy`

🔒 *安全审计*
• `SSH 端口`: `2222 ✅ 非标准端口`
• `PermitRootLogin`: `✅ prohibit-password`
• `暴力破解 (24h)`: `2 次`
• `防火墙`: `✅ ufw 已激活`
• `fail2ban`: `✅ 运行中 (已封禁 15 个 IP)`

📦 *更新状态*
• `待更新包`: `5 个 (安全更新: 2 个)`

✅ *一切正常，无需操作*
```

## 系统要求

- Linux (Ubuntu/Debian 推荐)
- Python 3.6+
- Docker (可选，用于容器检查)
- `ss`, `df`, `free`, `nproc`, `uptime` 等标准工具

## 许可

MIT License — 自由使用、修改、分发。
