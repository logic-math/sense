# 依赖关系
task1, task2, task3, task4

# 任务名称
集成验证：更新 mock_agent.py 和 integration_test.sh 覆盖所有 Bug 修复

# 任务目标
在 task1-4 的 Bug 修复完成后，更新 mock_agent.py 新增相关场景，并更新 integration_test.sh 覆盖所有修复点的端到端验证，确保回归测试完整。

# 关键结果
1. 更新 `tests/mock_agent/mock_agent.py`，新增场景：
   - `plan_comma_deps`：创建使用逗号分隔依赖的 task.md（`task1, task2`），验证 `sense doing dag` 能正确解析
   - `learning_readme`：在 `.sense/jobs/{job_id}/` 根目录创建 README.md（而非 learning/ 子目录）
2. 更新 `tests/integration_test.sh`，新增测试用例：
   - 逗号分隔依赖的 dag 生成（task1, task2 → tasks.json 包含正确依赖）
   - `sense doing update_task job_1 task1 success` 位置参数调用成功
   - `sense tools gen_prompt plan job_1` 输出到 `.sense/jobs/job_1/prompts/` 目录
   - `sense tools gen_prompt learning job_1` 生成的 prompt 不含 `{{job_summary}}` 字面量
   - `sense tools learning_check` 在 job 根目录有 README.md 时 PASS
3. 运行 `bash tests/integration_test.sh`，所有测试通过（包含新增用例）

# 测试方法
1. 运行 `python3 .sense/jobs/job_2/doing/tests/task5.py`，验证输出 `{"pass": true, "errors": []}`
2. 测试脚本覆盖：
   - `python3 tests/mock_agent/mock_agent.py --self-test` 输出 `OK: all self-tests passed`
   - `bash tests/integration_test.sh` 退出码 0，所有 PASS 行数 ≥ 原有数量 + 5（新增 5 个测试）
   - 无 FAIL 行
