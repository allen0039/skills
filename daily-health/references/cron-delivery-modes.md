# Cron 交付模式对比

## `no_agent: true`（推荐用于纯脚本输出）

**工作方式**：脚本 stdout 直推目标平台，无 LLM 参与。

```
script stdout → gateway delivery → 平台 adapter → 消息
```

**优点**：
- 零 token 消耗
- 输出确定性强，不会被 LLM 改写
- 执行快（无 LLM 推理延迟）

**关键限制**：
- `script` 字段必须是 `~/.hermes/scripts/` 下的**相对文件名**
- 必须是**实体文件**，符号链接会被拒绝
- 空 stdout = 静默运行（不推送任何消息）
- 非零退出码 = 错误告警推送

**配置示例**：
```yaml
no_agent: true
script: health_check.py          # ~/.hermes/scripts/health_check.py
deliver: telegram
```

## `no_agent: false`（默认，agent 模式）

**工作方式**：LLM 读取 prompt + 脚本输出（如有），生成回复推送。

**适用场景**：
- 需要 LLM 总结、分析、判断的场景
- 条件推送（某些情况不推送）
- 多数据源整合

## 注意事项

1. **符号链接被拒**：`ln -s` 创建的链接在 cron runner 中被安全检查拦截，必须 `cp` 实体文件
2. **调试输出泄漏**：`no_agent` 模式下脚本的 print 会直接出现在推送消息中，只 print 最终报告
3. **agent 模式不可靠**：LLM 可能改写格式，且 cron 注入的系统指令可能限制工具使用
