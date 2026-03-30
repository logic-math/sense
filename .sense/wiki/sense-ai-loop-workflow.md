# sense-ai-loop 工作流程

## 概述

sense-ai-loop 是 AI 编程自动循环，驱动 **plan → doing → learning** 完整流程。

触发方式（在 Claude Code 中）：
- `sense loop`
- `用 sense 实现 <需求>`
- `ai loop`
- `开始 sense 循环`

---

## 完整流程

### 第 0 步：初始化

1. 确认 `.sense/` 目录存在（否则运行 `sense init`）
2. 确定 job_id：`sense job list` 查看现有 job
3. 如果是新 job，准备输入文档（sense-express 文档或用户需求描述）

### 第 1 步：Plan 阶段

```bash
sense tools gen_prompt plan {job_id}
```

启动 **plan sub-agent**，读取 `prompts/plan_{job_id}.md`：
- 解析需求文档（why/how → task DAG）
- 产出：`.sense/jobs/{job_id}/plan/task*.md`

质量检查：
```bash
sense tools plan_check {job_id}
```
失败则重启 plan sub-agent 修复。

### 第 2 步：Doing 阶段

#### 生成 DAG
```bash
sense doing dag {job_id}
```
产出：`.sense/jobs/{job_id}/doing/tasks.json`

#### 任务循环
```
loop:
  task_id = $(sense doing next_task {job_id})
  if task_id == "NONE": break

  # 红阶段：生成测试
  sense tools gen_prompt test {job_id} {task_id}
  → test sub-agent 产出 doing/tests/{task_id}.py

  # 绿阶段：实现
  sense tools gen_prompt doing {job_id} {task_id}
  → doing sub-agent 实现代码 + worklog

  # 运行测试
  python3 .sense/jobs/{job_id}/doing/tests/{task_id}.py

  if 失败（最多重试 3 次）:
    → doing sub-agent（携带失败信息）修复代码
    → 重新运行测试

  # 提交
  git add -A
  git commit -m "feat({task_id}): {task_name}"
  sense doing update_task {job_id} {task_id} success --commit $(git rev-parse HEAD)
```

Doing 完成检查：
```bash
sense tools doing_check {job_id}
```

### 第 3 步：Learning 阶段

```bash
sense tools gen_prompt learning {job_id}
```

启动 **learning sub-agent**：
- 产出：`.sense/jobs/{job_id}/learning/README.md`（完整变更摘要）
- 产出：`learning/wiki/` 更新
- 产出：`learning/skills/` 更新

合并到项目上下文：
```bash
sense learning merge {job_id}
```

质量检查：
```bash
sense tools learning_check {job_id}
```

---

## 断点续跑

当 Claude Code 上下文压缩后，重新触发 `sense loop`：

1. `sense job list` → 查看 job 状态
2. `sense doing next_task {job_id}` → 确认当前进度
3. 从断点处继续（tasks.json 是唯一状态锚点）

---

## 失败处理

| 情况 | 处理方式 |
|------|----------|
| plan_check 失败 | 重启 plan sub-agent，携带失败原因 |
| 测试失败超过 3 次 | 暂停，向用户报告，等待人工干预 |
| doing_check 发现 zombie task | `sense doing update_task {job_id} {task_id} pending` 重置后继续 |
| learning_check 失败 | 重启 learning sub-agent |

---

## 子 Agent 调用规范

通过 Claude Code 的 Agent tool 启动：
```
Agent(
  prompt = <prompt 文件内容>,
  subagent_type = "general-purpose"
)
```

子 agent 完成后，主控 agent 验证产出文件存在再继续。

---

## 测试与验证

- **mock_agent.py**：`tests/mock_agent/mock_agent.py`，通过 `MOCK_SCENARIO` 环境变量模拟各阶段 sub-agent
- **集成测试**：`tests/integration_test.sh`，CI 环境无需 claude 命令
- **自测**：`python3 tests/mock_agent/mock_agent.py --self-test`
