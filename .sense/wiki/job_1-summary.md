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
