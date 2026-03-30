# Job job_2 执行摘要

## 完成时间
2026-03-30

## 实现了什么

- **task1**：修复 `internal/parser/task.go`，依赖关系解析支持逗号分隔（`task1, task2`）和换行分隔两种格式
- **task2**：修正 `skills/sense-ai-loop/SKILL.md` 中 `update_task` 的调用签名，从错误的 `--status` flag 形式改为正确的位置参数形式
- **task3**：修复 `internal/cmd/tools.go`，`gen_prompt learning` 阶段自动读取 `tasks.json` 和 `debug.md` 生成 `job_summary` 并注入 prompt
- **task4**：修复两个路径问题：`gen_prompt` 输出路径改为 `.sense/jobs/{job_id}/prompts/`；`learning_check` 的 README.md 检查路径改为 job 根目录；新增 `workspace.GetJobPromptsDir`
- **task5**：更新 `tests/mock_agent/mock_agent.py` 新增 `plan_comma_deps` 和 `learning_readme` 场景；更新 `tests/integration_test.sh` 新增 5 个测试，总测试数从 6 增至 18，全部通过

## 主要变更

### `internal/parser/task.go`
依赖关系解析逻辑从"整行作为一个 task_id"改为"按逗号拆分，trim 每个 token"，同时保持换行分隔的向后兼容。

### `skills/sense-ai-loop/SKILL.md`
doing 循环中 `update_task` 调用示例：
```bash
# 修复前（错误）
sense doing update_task {job_id} {task_id} --status success --commit $(git rev-parse HEAD)
# 修复后（正确）
sense doing update_task {job_id} {task_id} success --commit $(git rev-parse HEAD)
```

### `internal/cmd/tools.go`
1. 新增 `buildJobSummary(root, jobID)` 函数，读取 `tasks.json` + `debug.md` 拼接摘要
2. learning 阶段 `gen_prompt` 自动注入 `job_summary`
3. prompt 输出目录：`filepath.Join(cwd, "prompts")` → `workspace.GetJobPromptsDir(cwd, jobID)`
4. `learning_check` 的 README.md 路径：`learning/README.md` → `.sense/jobs/{job_id}/README.md`

### `internal/workspace/workspace.go`
新增 `GetJobPromptsDir(root, jobID string) string`

### `tests/mock_agent/mock_agent.py`
新增两个场景：
- `plan_comma_deps`：生成使用逗号分隔依赖的 task3.md（`task1, task2`）
- `learning_readme`：在 job 根目录生成 README.md（而非 learning/ 子目录）

### `tests/integration_test.sh`
新增 Test 7-11：
- Test 7：逗号分隔依赖的 dag 生成正确
- Test 8：`update_task` 位置参数 + `--commit` 正确执行
- Test 9：`gen_prompt` 输出到 `.sense/jobs/{job_id}/prompts/`
- Test 10：`gen_prompt learning` 中 `{{job_summary}}` 被替换，tasks.json 内容注入
- Test 11：`learning_check` 在 job 根目录有 README.md 时 PASS

## 遇到的问题和解决方案

### 问题 1：parser 整行作为依赖名
**现象**：`task4.md` 写 `task2, task3`，`BuildDAG` 报错找不到 `"task2, task3"` 这个 task。
**根因**：parser 按行读取，未做逗号拆分。
**修复**：每行先 `strings.Split(l, ",")` 再 `strings.TrimSpace` 每个 token。

### 问题 2：SKILL.md 与 CLI 实现不一致
**现象**：SKILL.md 写 `--status success`，但 CLI 实现是位置参数 `<status>`，导致 skill 驱动时命令失败。
**修复**：修改 SKILL.md 文档，与 CLI 实现对齐（CLI 实现本身是正确的）。

### 问题 3：learning prompt 变量未注入
**现象**：生成的 learning prompt 中 `{{job_summary}}` 原样保留，learning sub-agent 拿不到执行上下文。
**修复**：在 `gen_prompt` 的 learning 分支中调用 `buildJobSummary` 注入。

### 问题 4：路径不一致导致 learning_check 永远 FAIL
**现象**：`learning_check` 找 `learning/README.md`，但 learning sub-agent 规范产出的是 job 根目录的 `README.md`。
**修复**：将检查路径改为 `.sense/jobs/{job_id}/README.md`。

## 下次可以改进的地方

1. **job_2 的 tasks.json 是手工创建的**：因为 `sense doing dag` 依赖 parser，而 parser 在 task1 修复前无法解析逗号依赖。理想情况下应该先修复 parser，再用 `sense doing dag` 自动生成。未来可以考虑在 dag 生成失败时给出更友好的错误提示。

2. **learning_check 的 skills 路径**：当前检查 `learning/skills/*.py`，但 `learning_readme` 场景的 skills 也在 `learning/skills/`，两者一致。但 `learning merge` 命令合并的是 `learning/wiki/` 和 `learning/skills/`，这条路径是自洽的。

3. **prompt 模板语言是英文**：`gen_prompt` 生成的 prompt 文件标题和 Instructions 是英文，但项目语境是中文。后续可以考虑中文化模板，让 sub-agent 更自然地理解任务。

4. **`buildJobSummary` 没有 git log**：learning sub-agent 规范要求读取 `git log --oneline`，但当前 `buildJobSummary` 只读 tasks.json 和 debug.md，没有注入 git log。可以在后续迭代中补充。
