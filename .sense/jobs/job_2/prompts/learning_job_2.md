# Learning Phase Prompt

You are a senior engineer responsible for knowledge extraction. Your task is to summarize the job execution and update project documentation.

## Project Context

### OKR

# OKR — sense 项目

## Objective
构建 sense-ai-loop：一个人类帮助 AI 成长的循环。以结构化文档为输入，驱动 AI 自动完成软件开发任务，并将经验沉淀回项目上下文（wiki、skills、OKR、SPEC）。

## Key Results

### KR1：sense CLI 完整实现（已完成 job_1）
- [x] `sense init`：初始化 `.sense/` 工作空间
- [x] `sense doing dag <job_id>`：解析 plan/*.md → tasks.json
- [x] `sense doing next_task <job_id>`：返回下一个可执行 task
- [x] `sense doing update_task <job_id> <task_id> <status>`：更新任务状态
- [x] `sense doing list <job_id>`：展示任务状态表格
- [x] `sense job list`：列出所有 job
- [x] `sense tools gen_prompt <phase> <job_id> [task_id]`：生成各阶段 prompt
- [x] `sense tools plan_check / doing_check / learning_check`：质量门禁
- [x] `sense learning merge <job_id>`：合并 learning 产物到 .sense/

### KR2：sense-ai-loop skill 完整实现（已完成 job_1）
- [x] `skills/sense-ai-loop/SKILL.md`：主控循环
- [x] `skills/sense-ai-loop/skills/plan.md`：plan sub-agent 规则
- [x] `skills/sense-ai-loop/skills/doing.md`：doing sub-agent 规则
- [x] `skills/sense-ai-loop/skills/learning.md`：learning sub-agent 规则

### KR3：自举验证（已完成 job_1）
- [x] `tests/mock_agent/mock_agent.py`：模拟 sub-agent 文件系统操作
- [x] `tests/integration_test.sh`：端到端集成测试
- [x] `scripts/build.sh`：编译脚本

### KR4：后续迭代目标（待规划）
- [ ] review 阶段（SPEC 合规性检查）
- [ ] 更丰富的 prompt 模板（携带更多项目上下文）
- [ ] sense CLI 支持从 sense-express 文档直接解析生成 plan
- [ ] 与 sense-human-loop 深度集成


### SPEC

# SPEC — sense 项目编码规范

## 语言与模块
- **语言**：Go（module: `github.com/sunquan/sense`，go 1.25+）
- **CLI 框架**：cobra（`github.com/spf13/cobra`）
- **包结构**：
  - `cmd/sense/main.go`：入口
  - `internal/cmd/`：cobra 子命令（doing、job、learning、tools、init、root）
  - `internal/workspace/`：`.sense/` 目录管理
  - `internal/parser/`：task.md 解析
  - `internal/executor/`：DAG 调度、tasks.json 管理
  - `internal/prompt/`：prompt 模板渲染

## task.md 格式规范
每个 task.md 必须包含以下五个 section（`# ` 开头）：
```
# 依赖关系
（无）或 task1, task2

# 任务名称
简短描述

# 任务目标
详细说明要做什么

# 关键结果
1. 可验证的产出物

# 测试方法
1. 如何验证
```

## tasks.json 格式规范
```json
{
  "version": "1.0",
  "created_at": "...",
  "updated_at": "...",
  "tasks": [
    {
      "task_id": "task1",
      "task_name": "...",
      "task_file": "task1.md",
      "status": "pending|running|success|failed",
      "dependencies": [],
      "attempts": 0,
      "commit_hash": "",
      "created_at": "...",
      "updated_at": "..."
    }
  ]
}
```

## 文件写入规范
- tasks.json 写入必须原子化（先写 `.tmp`，再 `rename`）
- 所有写操作支持幂等

## 测试规范
- 每个 task 对应一个 Python 测试脚本（`doing/tests/{task_id}.py`）
- 测试脚本输出 JSON：`{"pass": true/false, "errors": [...]}`
- 集成测试脚本：`tests/integration_test.sh`，CI 环境无需 claude 命令

## prompt 模板规范
- 模板文件位于 `internal/prompt/templates/*.md`
- 通过 `//go:embed` 嵌入二进制
- 变量使用 `{{variable}}` 语法
- 所有 prompt 自动注入 OKR、SPEC、wiki、skills 上下文

## check 命令输出规范
- 默认输出：`PASS` 或 `FAIL: <reason>`，退出码 0/1
- `--json` flag：`{"pass": true/false, "errors": [...]}`

## Git 提交规范
- task 粒度提交：`feat({task_id}): {task_name}`
- 每个 task 完成后立即 commit，支持回滚


### Wiki

## cli-reference.md

# sense CLI 命令参考

## 安装

```bash
# 编译
bash scripts/build.sh        # 输出到 bin/sense

# 安装到 PATH
./install                    # 安装 CLI 到 ~/.local/bin/sense，安装 skills 到 ~/.claude/skills/
```

## 工作空间管理

### `sense init`
在当前目录初始化 `.sense/` 工作空间。

```bash
sense init
```

**创建结构：**
```
.sense/
  OKR.md
  SPEC.md
  wiki/
  skills/
  jobs/
```

**注意：** sense CLI 会在当前工作目录下寻找 `.sense/`，所有命令必须在包含 `.sense/` 的目录下运行（或其子目录）。实际上 sense 使用 `os.Getwd()` 作为项目根目录。

---

## Job 管理

### `sense job list`
列出所有 job 及其状态。

```bash
sense job list
```

**输出示例：**
```
JOB_ID       STATUS      TASKS
--------------------------------------------------
job_1        success     7/7 done
```

**状态推断逻辑：** 有 failed → failed；有 running → running；有 pending → pending；否则 → success。

---

## Doing 阶段

### `sense doing dag <job_id>`
解析 `.sense/jobs/{job_id}/plan/*.md`，生成 `doing/tasks.json`。

```bash
sense doing dag job_1
```

**前提：** plan 目录下存在 task*.md 文件。
**产出：** `.sense/jobs/job_1/doing/tasks.json`

### `sense doing next_task <job_id>`
返回下一个可执行的 task ID（所有依赖已 success 的第一个 pending task）。

```bash
sense doing next_task job_1
# 输出: task1（或 NONE）
```

### `sense doing update_task <job_id> <task_id> <status>`
更新 tasks.json 中指定 task 的状态。

```bash
sense doing update_task job_1 task1 success --commit abc1234
sense doing update_task job_1 task1 failed --attempts 2
```

**状态值：** `pending` | `running` | `success` | `failed`

### `sense doing list <job_id>`
以表格形式展示所有任务状态。

```bash
sense doing list job_1
```

---

## Learning 阶段

### `sense learning merge <job_id>`
将 learning 产物合并到 `.sense/` 项目上下文。

```bash
sense learning merge job_1
```

**合并规则：**
- `learning/wiki/` → `.sense/wiki/`（覆盖同名文件）
- `learning/skills/` → `.sense/skills/`
- `learning/OKR.md` / `learning/SPEC.md` → `.sense/OKR.md` / `.sense/SPEC.md`（直接覆盖）

---

## Tools 工具命令

### `sense tools gen_prompt <phase> <job_id> [task_id]`
生成指定阶段的 prompt 文件到 `prompts/` 目录。

```bash
sense tools gen_prompt plan job_1
sense tools gen_prompt doing job_1 task1
sense tools gen_prompt test job_1 task1
sense tools gen_prompt review job_1 task1
sense tools gen_prompt learning job_1
```

**prompt 自动注入：** OKR、SPEC、wiki、skills 内容。
**task 相关 prompt 额外注入：** task_name、task_goal、task_key_results、task_test_methods、test_script_path。

### `sense tools plan_check <job_id> [--json]`
验证 plan 目录质量。

**检查项：**
- plan/ 下存在至少一个 task*.md
- 每个 task.md 包含五个必要 section
- 依赖关系无循环

```bash
sense tools plan_check job_1
sense tools plan_check job_1 --json
# {"pass": true, "errors": []}
```

### `sense tools doing_check <job_id> [--json]`
验证 doing 目录质量。

**检查项：**
- tasks.json 存在且格式合法
- 无 zombie task（status=running 视为 zombie）

### `sense tools learning_check <job_id> [--json]`
验证 learning 产物质量。

**检查项：**
- `learning/README.md` 存在
- `learning/skills/*.py` 语法合法（`python3 -m py_compile`）

## job_1-summary.md

# job_1 完成摘要：sense CLI 初始实现

## 概述

**目标：** 从零实现 sense CLI（Go）+ sense-ai-loop skill，完成自举验证。

**完成时间：** 2026-03-28

**7 个 task 全部 success，耗时约 1 小时。**

---

## Task 完成情况

### task1：初始化 sense 项目结构
- `go.mod`（module: `github.com/sunquan/sense`）
- `internal/workspace/workspace.go`：Init、GetSenseDir、NextJobID、GetJobPlanDir/DoingDir/LearningDir、ListJobIDs
- `internal/parser/task.go`：ParseTaskFile（解析 5 个 section）
- `internal/cmd/root.go` + `cmd/sense/main.go`
- `internal/cmd/init.go`：`sense init` 子命令

**关键问题：** NextJobID 的 root 参数语义——传入 `.sense/` 目录（非项目根），查找 `<root>/jobs/`。

### task2：DAG 调度核心
- `internal/executor/dag.go`：BuildDAG，验证依赖存在 + 检测循环
- `internal/executor/topological.go`：Kahn 算法拓扑排序
- `internal/executor/tasks_json.go`：TasksJSON/TaskRecord，Load/Save/NewTasksJSON/UpdateStatus/UpdateCommit/UpdateAttempts/NextTask
- `internal/cmd/doing.go`：`sense doing dag/next_task/update_task/list`

### task3：prompt 模板系统
- `internal/prompt/context.go`：LoadContext，加载 OKR/SPEC/wiki/skills
- `internal/prompt/templates/*.md`：plan/doing/test/review/learning 模板
- `internal/prompt/builder.go`：`//go:embed` + `{{variable}}` 替换
- `internal/cmd/tools.go`：`sense tools gen_prompt`

### task4：tools check 命令
- `sense tools plan_check`：5 个 section 检查 + DAG 循环检测
- `sense tools doing_check`：zombie task 检测（status=running 视为 zombie）
- `sense tools learning_check`：README.md 存在 + Python 语法检查
- 所有 check 支持 `--json` flag

### task5：update_task + learning merge
- `sense doing update_task`：原子写入 tasks.json
- `sense learning merge`：wiki/skills/OKR/SPEC 合并
- `sense doing list`：任务状态表格
- `sense job list`：所有 job 状态

### task6：sense-ai-loop SKILL.md
- `skills/sense-ai-loop/SKILL.md`：主控循环
- `skills/sense-ai-loop/skills/plan.md`
- `skills/sense-ai-loop/skills/doing.md`
- `skills/sense-ai-loop/skills/learning.md`
- `install` 脚本注册

### task7：mock_agent.py + 集成测试
- `tests/mock_agent/mock_agent.py`：7 种场景（MOCK_SCENARIO 环境变量）
- `tests/integration_test.sh`：端到端测试
- `scripts/build.sh`：编译脚本

---

## 关键技术决策

1. **sense CLI 不调用 claude**：与 rick 最大区别，sub-agent 由 Claude Code Agent tool 驱动
2. **tasks.json 原子写入**：tmp + rename 防数据损坏
3. **模板嵌入二进制**：`//go:embed templates/*.md`，单文件分发
4. **zombie task 检测**：任何 status=running 的 task 都视为 zombie（无法追踪 PID）

---

## Commit 记录

| task | commit |
|------|--------|
| task1 | 366030f |
| task2 | e805612 |
| task3 | 3b61f5d |
| task4 | 8e1fa0b |
| task5 | 512f5fd |
| task6 | a423a58 |
| task7 | 5b70920 |

## sense-ai-loop-workflow.md

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

## task-md-format.md

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
- 多依赖：`task2, task3`（逗号分隔，但 parser 实际按行读取）

**注意：** parser 按行读取依赖，每行一个 task_id。逗号分隔在 plan 文件中常见，但 parser 不自动拆分逗号——实际上 `.rick/jobs/job_1/plan/` 中的文件使用 `task2, task3` 格式，而 parser 将整行作为一个依赖名。**这是一个已知的语义问题**，在 job_1 中通过 BuildDAG 的依赖验证会报错（找不到 "task2, task3"）。

**实际 job_1 中的处理：** doing.go 在调用 ParseTaskFile 后直接使用 `task.Dependencies`，而 task.md 中的依赖行是 `task2, task3`，这会导致 DAG 构建失败。**后续需要修复 parser 以支持逗号分隔的依赖列表。**

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
- 依赖关系：非空行且非 `（无）` 的行作为依赖 task_id

## architecture.md

# sense 项目架构

## 项目定位

sense 是一个基于 SENSE 方法论的 AI 编程框架，核心是 **sense-ai-loop**：人类通过 sense-human-loop 想清楚需求，AI 通过 sense-ai-loop 自动完成软件开发，经验沉淀回项目上下文形成闭环。

```
人类思考（sense-human-loop）
    ↓ sense-express 文档
AI 编程（sense-ai-loop）
    ↓ 代码 + 知识
项目上下文（.sense/wiki、skills、OKR、SPEC）
    ↑ 下次循环输入
```

## 系统组成

### sense CLI（Go）
核心工具，负责工作空间管理、prompt 生成、质量检查、DAG 调度。

**模块结构：**
```
cmd/sense/main.go              # 入口
internal/
  cmd/                         # cobra 子命令
    root.go                    # 根命令（version 0.1.0）
    init.go                    # sense init
    doing.go                   # sense doing dag/next_task/update_task/list
    job.go                     # sense job list
    learning.go                # sense learning merge
    tools.go                   # sense tools gen_prompt/plan_check/doing_check/learning_check
  workspace/workspace.go       # .sense/ 目录管理
  parser/task.go               # task.md 解析
  executor/
    dag.go                     # DAG 构建
    topological.go             # Kahn 拓扑排序
    tasks_json.go              # tasks.json 读写
  prompt/
    context.go                 # 项目上下文加载
    builder.go                 # 模板渲染（//go:embed）
    templates/                 # plan/doing/test/review/learning.md 模板
```

### sense-ai-loop skill（Claude Code）
告诉 Claude Code 如何驱动 sense CLI 完成 plan → doing → learning 循环。

```
skills/
  sense-ai-loop/
    SKILL.md                   # 主控循环（触发词：sense loop、用 sense 实现）
    skills/
      plan.md                  # plan sub-agent 规则
      doing.md                 # doing sub-agent 规则
      learning.md              # learning sub-agent 规则
  sense-human-loop/
    SKILL.md                   # 深度思考循环
    skills/
      sense-think/SKILL.md
      sense-learn/SKILL.md
      sense-express/SKILL.md
```

### .sense/ 工作空间
```
.sense/
  OKR.md                       # 项目目标（跨 job 持续更新）
  SPEC.md                      # 编码规范（每次 doing 必须遵循）
  wiki/                        # 项目知识库（learning 持续更新）
  skills/                      # 项目工具描述文件
  jobs/
    job_1/
      plan/                    # task*.md + tasks.json（plan 阶段产出）
      doing/
        tasks.json             # DAG 调度元信息（唯一状态锚点）
        tests/                 # Python 测试脚本
```

## 核心设计决策

### 1. sense CLI 不调用 claude 命令
与前身 rick 不同，sense CLI 只做文件管理 + prompt 生成 + check，不启动 claude 子进程。真正的 AI 执行由 Claude Code 的 Agent tool（sub-agent）完成。

### 2. tasks.json 是唯一状态锚点
当 Claude Code 上下文压缩后，通过 `sense doing next_task` 读取 tasks.json 恢复执行进度，不依赖对话历史。

### 3. 项目本身就是记忆系统
每次 job 完成后，learning 阶段将变更合并到 .sense/wiki/ 和 .sense/skills/，使下一次 job 的 AI 执行精度持续提升。

### 4. 原子写入
tasks.json 写入通过"先写 .tmp，再 rename"保证原子性，防止进程中断导致数据损坏。



### Skills



## Job Summary

**Job ID**: job_2

## tasks.json

```json
{
  "version": "1.0",
  "created_at": "2026-03-30T10:00:00+08:00",
  "updated_at": "2026-03-30T18:30:37.626353718+08:00",
  "tasks": [
    {
      "task_id": "task1",
      "task_name": "修复 parser 不支持逗号分隔依赖的 Bug",
      "task_file": "task1.md",
      "status": "success",
      "dependencies": null,
      "attempts": 0,
      "commit_hash": "a54d19d81953c5806fee17e330c3af06fce2666b",
      "created_at": "2026-03-30T10:00:00+08:00",
      "updated_at": "2026-03-30T18:25:52.419999277+08:00"
    },
    {
      "task_id": "task2",
      "task_name": "修复 update_task 命令签名与 SKILL.md 不一致的 Bug",
      "task_file": "task2.md",
      "status": "success",
      "dependencies": null,
      "attempts": 0,
      "commit_hash": "a54d19d81953c5806fee17e330c3af06fce2666b",
      "created_at": "2026-03-30T10:00:00+08:00",
      "updated_at": "2026-03-30T18:25:52.496251745+08:00"
    },
    {
      "task_id": "task3",
      "task_name": "修复 learning prompt 缺少 job_summary 变量注入",
      "task_file": "task3.md",
      "status": "success",
      "dependencies": null,
      "attempts": 0,
      "commit_hash": "a54d19d81953c5806fee17e330c3af06fce2666b",
      "created_at": "2026-03-30T10:00:00+08:00",
      "updated_at": "2026-03-30T18:25:52.634754803+08:00"
    },
    {
      "task_id": "task4",
      "task_name": "修复 gen_prompt 输出路径和 learning_check 路径不符合设计规范",
      "task_file": "task4.md",
      "status": "success",
      "dependencies": null,
      "attempts": 0,
      "commit_hash": "a54d19d81953c5806fee17e330c3af06fce2666b",
      "created_at": "2026-03-30T10:00:00+08:00",
      "updated_at": "2026-03-30T18:25:52.71114855+08:00"
    },
    {
      "task_id": "task5",
      "task_name": "集成验证：更新 mock_agent.py 和 integration_test.sh 覆盖所有 Bug 修复",
      "task_file": "task5.md",
      "status": "success",
      "dependencies": [
        "task1",
        "task2",
        "task3",
        "task4"
      ],
      "attempts": 0,
      "commit_hash": "c407258615a7623cdac279ef5a3e962b20e68ed8",
      "created_at": "2026-03-30T10:00:00+08:00",
      "updated_at": "2026-03-30T18:30:37.626353288+08:00"
    }
  ]
}
```



## Instructions

Based on the job execution, update the following:

1. **README.md**: Update project README with new features and usage
2. **Wiki**: Update `.sense/wiki/` with new knowledge and patterns discovered
3. **Skills**: Update `.sense/skills/` with reusable skill patterns

Focus on:
- What worked well and should be repeated
- What failed and how it was fixed
- New patterns or techniques discovered
- Improvements to existing processes
