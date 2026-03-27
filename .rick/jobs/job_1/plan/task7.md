# 依赖关系
task1, task2, task3, task4, task5

# 任务名称
编写 mock_agent.py 和集成测试（自举验证 sense CLI）

# 任务目标
编写 `tests/mock_agent/mock_agent.py`，模拟 sense-ai-loop skill 中各阶段 sub-agent 的文件系统操作，用于在不调用真实 Claude 的情况下验证 sense CLI 的完整工作流。同时编写集成测试脚本验证 plan → doing → learning 全流程。

# 关键结果
1. 创建 `tests/mock_agent/mock_agent.py`，支持以下场景（通过 `MOCK_SCENARIO` 环境变量切换）：
   - `plan_success`：在 plan 目录创建合法的 task1.md、task2.md
   - `plan_missing_section`：创建缺少必要 section 的 task.md
   - `plan_circular_dep`：创建循环依赖的 task*.md
   - `doing_success`：在 doing/task1/ 目录创建 doing1.md（worklog）
   - `test_success`：在 doing/task1/ 目录创建 test1.py（输出 `{"pass": true, "errors": []}`）
   - `test_fail`：创建 test1.py（输出 `{"pass": false, "errors": ["assertion failed"]}`）
   - `learning_success`：在 learning/ 目录创建 README.md、wiki/arch.md、skills/check.py
2. 创建 `tests/integration_test.sh`：端到端集成测试脚本，覆盖：
   - `sense init` → `sense doing dag` → `sense doing next_task` → `sense doing update_task` → 循环直到 NONE
   - `sense tools plan_check` 通过/失败场景
   - `sense tools doing_check` zombie task 检测
   - `sense learning merge` 合并验证
3. mock_agent.py 支持 `--self-test` 模式（自我验证所有场景的产物正确性）
4. 集成测试在 CI 环境（无 Claude）中可完整运行（不依赖 claude 命令）
5. 创建 `scripts/build.sh`：编译 sense 到 `bin/sense`

# 测试方法
1. 运行 `python3 tests/mock_agent/mock_agent.py --self-test`，验证输出 `OK: all self-tests passed`
2. 运行 `bash tests/integration_test.sh`，验证所有测试通过（退出码 0）
3. 验证集成测试覆盖 `sense doing dag` + `sense doing next_task` 完整调度循环（task1→task2→NONE）
4. 验证 `sense tools plan_check` 对 plan_missing_section 场景返回 FAIL
5. 验证 `sense tools doing_check` 对 zombie task 场景返回 FAIL，并能自动恢复（重置为 pending）
