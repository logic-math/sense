# 依赖关系
（无）

# 任务名称
修复 parser 不支持逗号分隔依赖的 Bug

# 任务目标
`internal/parser/task.go` 中 ParseTaskFile 按行读取依赖关系，导致 `task1, task2` 整行被当成一个依赖名，BuildDAG 报错找不到对应 task。需要修复 parser，使其同时支持逗号分隔和换行分隔两种格式。

# 关键结果
1. 修改 `internal/parser/task.go` 中依赖关系解析逻辑：每行先按逗号拆分，再 trim 每个 token，过滤空值和 `（无）`/`(无)`
2. `go build ./...` 编译通过
3. 新增测试用例覆盖：逗号分隔（`task1, task2`）、换行分隔、混合格式、`（无）` 无依赖

# 测试方法
1. 运行 `python3 .sense/jobs/job_2/doing/tests/task1.py`，验证输出 `{"pass": true, "errors": []}`
2. 测试脚本覆盖：
   - 逗号分隔依赖（`task1, task2`）被正确解析为 `["task1", "task2"]`
   - 换行分隔依赖被正确解析
   - `（无）` 解析为空依赖列表
   - job_1 的 task4.md（`task2, task3`）能被 `sense doing dag` 正确处理（不报错）
