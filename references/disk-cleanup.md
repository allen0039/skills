# Disk Cleanup Workflow

当磁盘空间不足时，按以下流程清理。

## Step 1: 诊断

```bash
# 整体使用情况
df -h /

# 顶层目录大小
du -sh /* 2>/dev/null | sort -rh | head -20

# 详细查看 /var（通常是最大目录）
du -sh /var/*/ 2>/dev/null | sort -rh | head -10
du -sh /var/lib/*/ 2>/dev/null | sort -rh | head -10
du -sh /var/log/*/ 2>/dev/null | sort -rh | head -10

# Docker 空间
docker system df

# 用户目录（替换为你的实际用户名）
du -sh ~/*/ ~/.cache/ ~/.local/ 2>/dev/null | sort -rh | head -15
```

## Step 2: 清理（按安全级别排序）

### 2a. Docker 清理（最安全，收益最大）
```bash
# 移除未使用的镜像、构建缓存、网络
docker system prune -af
# 注意: -a 移除所有未使用的镜像, -f 跳过确认
# 仅移除未被运行中容器使用的资源
```

### 2b. Journal 日志（通常 1-4G）
```bash
# 压缩到 200MB（保留近期日志，删除旧日志）
journalctl --vacuum-size=200M
```

# 用户缓存
```bash
# 先检查大小
du -sh ~/.cache/
# 较大时可安全清除
rm -rf ~/.cache/*
```

### 2d. Snap 旧版本
```bash
snap list --all | awk '/disabled/{print $1, $3}' | while read name rev; do
  snap remove "$name" --revision="$rev"
done
```

### 2e. APT 缓存
```bash
apt clean
```

## Step 3: 验证

```bash
df -h /
```

## 典型清理效果（45G 磁盘, 69% 使用率）

- Docker prune: ~3-5G
- Journal vacuum: ~3-4G
- .cache: ~1-2G
- Snap + apt: ~500M
- **总计: ~8-10G**

## 注意事项

- `docker system prune -af` 是安全的 — 只移除悬挂/未使用的资源，不影响运行中容器
- Journal vacuum 保留近期日志；200MB 足够保存数周历史
- 不要删除系统关键目录（如 `/var/log/auth.log`）
