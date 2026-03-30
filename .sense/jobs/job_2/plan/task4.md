# 依赖关系
（无）

# 任务名称
修复 gen_prompt 输出路径和 learning_check 路径不符合设计规范

# 任务目标
存在两个路径相关 Bug：
1. `sense tools gen_prompt` 将 prompt 输出到 `<cwd>/prompts/`，应改为 `.sense/jobs/{job_id}/prompts/`
2. `sense tools learning_check` 验证 `learning/README.md`，但 learning sub-agent 规范产出的是 `.sense/jobs/{job_id}/README.md`（job 根目录），路径不一致导致 learning_check 永远 FAIL

# 关键结果
1. 修改 `internal/cmd/tools.go` 中 gen_prompt 的输出路径：改为 `.sense/jobs/{job_id}/prompts/{phase}_{task_id}.md`（通过 `workspace.GetJobPromptsDir` 或直接拼接）
2. 修改 `internal/cmd/tools.go` 中 learning_check：README.md 检查路径改为 `.sense/jobs/{job_id}/README.md`；skills 检查路径改为 `.sense/jobs/{job_id}/learning/skills/`（与 learning sub-agent 规范一致）
3. 同步修改 `internal/workspace/workspace.go`，新增 `GetJobPromptsDir(root, jobID string) string` 函数
4. `go build ./...` 编译通过

# 测试方法
1. 运行 `python3 .sense/jobs/job_2/doing/tests/task4.py`，验证输出 `{"pass": true, "errors": []}`
2. 测试脚本覆盖：
   - 运行 `sense tools gen_prompt plan job_1`，验证 prompt 文件输出到 `.sense/jobs/job_1/prompts/plan_job_1.md`，而非 `<cwd>/prompts/`
   - 运行 `sense tools gen_prompt doing job_1 task1`，验证输出到 `.sense/jobs/job_1/prompts/doing_job_1_task1.md`
   - 创建 `.sense/jobs/job_1/README.md`，运行 `sense tools learning_check job_1`，验证退出码 0（PASS）
   - 不创建 README.md，运行 learning_check，验证退出码 1（FAIL）且错误信息包含正确路径
