# 依赖关系
（无）

# 任务名称
修复 update_task 命令签名与 SKILL.md 不一致的 Bug

# 任务目标
`sense doing update_task` 的实际 CLI 签名是 `<job_id> <task_id> <status>`（status 为位置参数），但 SKILL.md 中写的是 `--status success --commit <hash>`（status 为 flag）。主控 skill 调用时会直接失败。需要同时修复 CLI 实现和 SKILL.md，统一为位置参数形式（与现有实现一致，修改 SKILL.md 中的调用示例）。

# 关键结果
1. 修改 `skills/sense-ai-loop/SKILL.md` 中 doing 循环的 update_task 调用示例，改为：
   `sense doing update_task {job_id} {task_id} success --commit $(git rev-parse HEAD)`
2. 同步修改 `skills/sense-ai-loop/skills/doing.md` 中的相关描述（如有）
3. 确认 CLI 实现本身（`internal/cmd/doing.go`）无需修改，当前位置参数实现是正确的

# 测试方法
1. 运行 `python3 .sense/jobs/job_2/doing/tests/task2.py`，验证输出 `{"pass": true, "errors": []}`
2. 测试脚本覆盖：
   - `sense doing update_task job_1 task1 success` 能正确执行（退出码 0）
   - `sense doing update_task job_1 task1 success --commit abc1234` 能正确执行
   - tasks.json 中 task1 的 status 被正确更新为 success
   - SKILL.md 中不再包含 `--status` flag 写法
