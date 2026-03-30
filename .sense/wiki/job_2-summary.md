# job_2 完成摘要：Bug 修复与测试补全

## 概述

**目标：** 修复 job_1 遗留的 5 个 Bug，补全集成测试覆盖。

**完成时间：** 2026-03-30

**5 个 task 全部 success，2 个 commit。**

---

## Task 完成情况

### task1：修复 parser 逗号分隔依赖
`internal/parser/task.go` 依赖解析：每行按逗号拆分后 trim，支持 `task1, task2` 和换行两种格式。

### task2：修正 SKILL.md update_task 签名
`skills/sense-ai-loop/SKILL.md`：`--status success` → `success`（位置参数）。

### task3：注入 learning job_summary
`internal/cmd/tools.go`：新增 `buildJobSummary()`，learning phase 自动注入 tasks.json + debug.md 内容。

### task4：修复路径规范
- `gen_prompt` 输出：`<cwd>/prompts/` → `.sense/jobs/{job_id}/prompts/`
- `learning_check` README 路径：`learning/README.md` → `.sense/jobs/{job_id}/README.md`
- `workspace.go` 新增 `GetJobPromptsDir`

### task5：集成验证
- `mock_agent.py` 新增 `plan_comma_deps`、`learning_readme` 场景
- `integration_test.sh` 新增 Test 7-11，总测试数 6 → 18，全部通过

---

## Commit 记录

| tasks | commit |
|-------|--------|
| task1-4 | a54d19d |
| task5 | c407258 |
