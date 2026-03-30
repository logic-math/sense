# 依赖关系
（无）

# 任务名称
修复 learning prompt 缺少 job_summary 变量注入

# 任务目标
`internal/prompt/templates/learning.md` 中使用了 `{{job_summary}}` 变量，但 `internal/cmd/tools.go` 的 `gen_prompt` 实现中，learning 阶段没有注入该变量，导致生成的 prompt 里 `{{job_summary}}` 原样保留，learning sub-agent 拿不到执行摘要。需要在 gen_prompt 的 learning 阶段自动读取 tasks.json 和 debug.md 生成 job_summary 并注入。

# 关键结果
1. 修改 `internal/cmd/tools.go` 中 gen_prompt 的 learning 阶段：自动读取 `.sense/jobs/{job_id}/doing/tasks.json` 和 `.sense/jobs/{job_id}/doing/debug.md`，拼接为 job_summary 字符串并注入到模板变量中
2. 如果 debug.md 不存在，job_summary 只包含 tasks.json 摘要
3. `go build ./...` 编译通过

# 测试方法
1. 运行 `python3 .sense/jobs/job_2/doing/tests/task3.py`，验证输出 `{"pass": true, "errors": []}`
2. 测试脚本覆盖：
   - 创建包含 tasks.json（所有 task success）和 debug.md 的 job，运行 `sense tools gen_prompt learning job_1`，验证生成的 prompt 文件中不含 `{{job_summary}}` 字面量
   - 验证生成的 prompt 包含 tasks.json 中的 task 名称
   - 验证 debug.md 不存在时，命令仍然成功（退出码 0），prompt 包含 tasks.json 摘要
