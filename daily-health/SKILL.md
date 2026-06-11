---
name: daily-health
description: >
  每天早上自动执行系统健康检查，生成结构化报告。
  检查项目：系统信息、监听端口、Docker 容器、安全审计、更新状态。
  纯只读检查，不会修改任何配置。Markdown 格式，反引号包裹可复制值。
tags: [devops, health-check, cron, monitoring]
triggers:
  - 检查系统健康
  - 系统状态报告
  - health check
  - 日常巡检
---

# Daily Health Check

每天早上自动执行的系统健康检查任务。

## 检查项目

| 模块 | 检查内容 |
|------|----------|
| 📋 系统信息 | 系统版本、内核、运行时间、负载、CPU、磁盘、内存、Swap |
| 🌐 监听端口 | 端口→服务映射，loopback/公网标识，去重 IPv4/IPv6 |
| 🐳 容器服务 | Docker 容器状态、健康检查 |
| 🔒 安全审计 | SSH 端口、PermitRootLogin、暴力破解、防火墙、公网暴露端口 |
| 📦 更新状态 | 待更新包数量、安全更新分类 |
| ⚠️ 建议 | 自动生成优化建议 |

## 输出风格

- **监听端口**：只给总数，不逐个列举（如 `16 个 (其中 4 个仅本地)`）
- **容器状态**：只显示 healthy / running / stopped，**不显示运行时长**
- **更新状态**：只显示包数量 + 安全更新数，**不列出具体包名**
- **建议**：不提示"系统需要重启"，只保留用户能操作的建议
- **fail2ban**：必须检测是否已安装再建议，避免误报
- **不保存报告文件**：脚本只 stdout 输出

## 使用方法

### 手动执行

```bash
python3 ~/.hermes/skills/<category>/daily-health/scripts/health_check.py
```

### 配合 Hermes Cron 使用

在 Hermes Agent 中创建定时任务：

```yaml
# 每天早上 08:00 (UTC+8) 执行
schedule: "0 8 * * *"
deliver: telegram
script: health_check.py
no_agent: true
```

脚本需复制到 `~/.hermes/scripts/` 目录：

```bash
cp ~/.hermes/skills/<category>/daily-health/scripts/health_check.py ~/.hermes/scripts/health_check.py
```

## 自定义端口映射

编辑 `scripts/health_check.py` 中的 `PORT_SERVICE_MAP` 字典，添加你的服务端口：

```python
PORT_SERVICE_MAP = {
    22: "SSH",
    80: "HTTP",
    443: "HTTPS",
    8080: "你的自定义服务",
}
```

## 参考文档

- [磁盘清理流程](references/disk-cleanup.md)
- [Cron 交付模式对比](references/cron-delivery-modes.md)
