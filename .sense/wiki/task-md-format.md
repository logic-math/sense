# task.md 格式规范

task.md 是 sense-ai-loop 的核心输入单元，由 plan sub-agent 生成，由 sense CLI 解析。

## 完整格式

```markdown
# 依赖关系
（无）

# 任务名称
简短描述（一行）

# 任务目标
详细说明要做什么，背景，为什么这样设计。

# 关键结果
1. 可验证的产出物 1
2. 可验证的产出物 2
3. ...

# 测试方法
1. 如何验证产出物 1
2. 如何验证产出物 2
3. ...
```

## 依赖关系语法

- 无依赖：`（无）` 或 `(无)`
- 单依赖：`task1`
- 多依赖：`task1, task2`（逗号分隔，同行）或每行一个

**parser 支持两种格式**（job_2/task1 修复后）：
- 逗号分隔：`task1, task2` → 解析为 `["task1", "task2"]`
- 换行分隔：每行一个 task_id
- 混合格式也支持

## 五个必要 Section

plan_check 验证每个 task.md 必须包含：
1. `# 依赖关系`
2. `# 任务名称`
3. `# 任务目标`
4. `# 关键结果`
5. `# 测试方法`

缺少任何一个 section 都会导致 plan_check FAIL。

## Parser 实现细节

`internal/parser/task.go`：
- 按 `# ` 前缀识别 section 标题
- 每个 section 收集后续所有行直到下一个 section
- `trimLines`：去除首尾空行，trim 每行空白
- 依赖关系：每行先按逗号拆分，再 trim 每个 token，过滤空值和 `（无）`/`(无)`
