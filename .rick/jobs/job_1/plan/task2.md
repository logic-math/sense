# 依赖关系
task1

# 任务名称
实现 DAG 调度核心（dag + topological + tasks_json）

# 任务目标
实现 `sense doing dag <job_id>` 和 `sense doing next_task <job_id>` 两个子命令。这两个命令是 doing 循环的调度引擎：dag 将 plan/*.md 解析为 tasks.json，next_task 根据 tasks.json 返回下一个可执行的 task ID。

# 关键结果
1. 实现 `internal/executor/dag.go`：从 parser.Task 列表构建 DAG，检测循环依赖
2. 实现 `internal/executor/topological.go`：Kahn 算法拓扑排序
3. 实现 `internal/executor/tasks_json.go`：TasksJSON 结构体、Load/Save/UpdateStatus/UpdateCommit 等方法，格式与 rick 完全一致
4. 实现 `sense doing dag <job_id>` 子命令：读 plan/*.md → 构建 DAG → 拓扑排序 → 生成 tasks.json 到 `doing/` 目录
5. 实现 `sense doing next_task <job_id>` 子命令：读 tasks.json，返回第一个所有依赖都已 success 的 pending task ID，无则输出 `NONE`

# 测试方法
1. Python 脚本：创建含 task1.md（无依赖）、task2.md（依赖 task1）的 plan 目录，运行 `sense doing dag job_1`，验证生成的 tasks.json 结构正确（version、tasks 数组、status 均为 pending）
2. Python 脚本：验证循环依赖的 plan 目录运行 `sense doing dag` 时返回非零退出码并输出错误信息
3. Python 脚本：手动写 tasks.json（task1=pending, task2=pending），运行 `sense doing next_task job_1`，验证输出为 `task1`
4. Python 脚本：手动写 tasks.json（task1=success, task2=pending），运行 `sense doing next_task job_1`，验证输出为 `task2`
5. Python 脚本：手动写 tasks.json（所有 task=success），运行 `sense doing next_task job_1`，验证输出为 `NONE`
