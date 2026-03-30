---
name: sense-ai-loop
description: "sense-ai-loop 是 AI 编程自动循环入口，驱动 plan → doing → learning 完整流程。触发词：sense loop、用 sense 实现、ai loop、开始 sense 循环、执行 sense job。输入：sense-express 产出的结构化文档（或用户直接描述需求）。输出：完整的软件实现 + 项目知识沉淀。"
---

# sense-ai-loop — 主控 Agent

## 使用契约

**你触发了 sense-ai-loop。**

这是一个 AI 编程自动循环，将驱动 plan → doing → learning 完整执行，直到 job 完成。

**前提条件：** 当前目录已运行 `sense init`（存在 `.sense/` 目录）。

---

## 三个阶段概述

| 阶段 | 工具 | 产出 |
|------|------|------|
| **Plan** | plan sub-agent | `.sense/jobs/{job_id}/plan/task*.md` |
| **Doing** | doing sub-agent × N | 代码实现 + `tasks.json` 状态 |
| **Learning** | learning sub-agent | `README.md` + wiki + skills 更新 |

---

## 主控循环流程

### 第 0 步：初始化

1. 确认 `.sense/` 目录存在，否则提示用户运行 `sense init`
2. 确定 job_id：运行 `sense job list` 查看现有 job，或创建新 job
3. 如果是新 job，确认输入文档路径（sense-express 产出文档或用户描述）

### 第 1 步：Plan 阶段

如果 `.sense/jobs/{job_id}/plan/` 目录为空或不存在：

```bash
sense tools gen_prompt plan {job_id}
```

启动 **plan sub-agent**（见 `skills/plan.md`）：
- 输入：plan prompt 文件（`prompts/plan.md`）
- 产出：`plan/task*.md` 文件（完整 task DAG）

Plan 完成后运行检查：
```bash
sense tools plan_check {job_id}
```

如果 plan_check 失败，重新启动 plan sub-agent 修复问题。

### 第 2 步：Doing 阶段（主循环）

#### 2.1 生成 DAG

```bash
sense doing dag {job_id}
```

产出：`.sense/jobs/{job_id}/doing/tasks.json`

#### 2.2 任务循环

```
loop:
  task_id = $(sense doing next_task {job_id})
  if task_id == "NONE": break

  # 红阶段：生成测试
  sense tools gen_prompt test {job_id} {task_id}
  启动 test sub-agent → 产出 doing/tests/{task_id}.py

  # 绿阶段：实现
  sense tools gen_prompt doing {job_id} {task_id}
  启动 doing sub-agent → 实现代码 + worklog

  # 运行测试
  result = python3 .sense/jobs/{job_id}/doing/tests/{task_id}.py

  if result.pass == false:
    # debug 循环（最多 3 次）
    sense tools gen_prompt doing {job_id} {task_id}
    启动 doing sub-agent（携带失败信息）→ 修复代码
    result = python3 .sense/jobs/{job_id}/doing/tests/{task_id}.py
    重复直到通过或超过重试限制

  # 提交
  git add -A
  git commit -m "feat({task_id}): {task_name}"
  sense doing update_task {job_id} {task_id} success --commit $(git rev-parse HEAD)
```

#### 2.3 Doing 完成检查

```bash
sense tools doing_check {job_id}
```

所有任务 success 后进入 Learning 阶段。

### 第 3 步：Learning 阶段

```bash
sense tools gen_prompt learning {job_id}
```

启动 **learning sub-agent**（见 `skills/learning.md`）：
- 产出：`job_{id}/README.md`（完整变更摘要）
- 产出：`.sense/wiki/` 更新
- 产出：`.sense/skills/` 更新

Learning 完成后运行检查：
```bash
sense tools learning_check {job_id}
```

---

## 上下文恢复（断点续跑）

当 Claude Code 上下文压缩后，重新触发 `sense loop` 时：

1. 运行 `sense job list` 查看 job 状态
2. 运行 `sense doing next_task {job_id}` 确认当前进度
3. 从断点处继续执行（tasks.json 是持久化状态）

**tasks.json 是唯一的状态锚点**，不依赖对话历史。

---

## 子 Agent 调用规范

所有子 agent 通过 Agent tool 启动，传入对应的 prompt 文件内容：

```
Agent(
  prompt = <prompt 文件内容>,
  subagent_type = "general-purpose"
)
```

每个子 agent 完成后，主控 agent 验证产出文件是否存在，再继续下一步。

---

## 失败处理

| 情况 | 处理方式 |
|------|----------|
| plan_check 失败 | 重新启动 plan sub-agent，携带失败原因 |
| 测试失败超过 3 次 | 暂停，向用户报告，等待人工干预 |
| doing_check 发现 zombie task | 重置 task 状态后继续 |
| learning_check 失败 | 重新启动 learning sub-agent |

---

## 子 Agent 文件位置

- Plan sub-agent：`skills/plan.md`
- Doing sub-agent：`skills/doing.md`
- Learning sub-agent：`skills/learning.md`
