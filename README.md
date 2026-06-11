# 🛠️ Skills

个人 Hermes Agent Skill 库 — 可复用的自动化技能集合。

## 📦 Skills 列表

| Skill | 描述 | 分类 |
|-------|------|------|
| [daily-health](daily-health/) | 🩺 轻量级 Linux 系统健康检查 | devops |

## 🚀 快速使用

### 作为 Hermes Skill

```bash
# 克隆整个仓库
git clone https://github.com/allen0039/skills.git ~/.hermes/skills/custom

# 或只复制单个 skill
git clone https://github.com/allen0039/skills.git /tmp/skills
cp -r /tmp/skills/daily-health ~/.hermes/skills/devops/
```

### 独立使用

每个 skill 目录下都有独立的 `README.md`，可以单独使用。

## 📁 结构

```
skills/
├── README.md              ← 你在这里
├── daily-health/
│   ├── README.md          # 使用说明
│   ├── SKILL.md           # Hermes Skill 定义
│   ├── scripts/           # 可执行脚本
│   └── references/        # 参考文档
├── skill-2/
│   └── ...
└── skill-3/
    └── ...
```

## 🤝 贡献

欢迎 Issue 和 PR！添加新 skill 请遵循：
1. 每个 skill 一个目录
2. 包含 `SKILL.md`（Hermes 格式）
3. 包含 `README.md`（使用说明）
4. 脚本放 `scripts/`，文档放 `references/`

## 📄 许可

MIT License — 自由使用、修改、分发。
