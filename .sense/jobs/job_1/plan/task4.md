# 依赖关系
task2, task3

# 任务名称
实现 tools check 命令（plan_check / doing_check / learning_check）

# 任务目标
实现 `sense tools plan_check <job_id>`、`sense tools doing_check <job_id>`、`sense tools learning_check <job_id>` 三个质量检查命令。这些命令由 sense-ai-loop skill 在各阶段完成后调用，验证 AI sub-agent 的产物是否符合规范，是 sense 循环的质量门禁。

# 关键结果
1. 实现 `sense tools plan_check <job_id>`：
   - 验证 plan/ 目录下存在至少一个 task*.md 文件
   - 验证每个 task.md 包含五个必要 section（依赖关系、任务名称、任务目标、关键结果、测试方法）
   - 验证依赖关系无循环（复用 DAG 逻辑）
   - 输出：`PASS` 或 `FAIL: <reason>`，退出码 0/1
2. 实现 `sense tools doing_check <job_id>`：
   - 验证 doing/ 目录下 tasks.json 存在且格式合法
   - 验证无 zombie task（status=running 但进程不存在）
   - 输出：`PASS` 或 `FAIL: <reason>`，退出码 0/1
3. 实现 `sense tools learning_check <job_id>`：
   - 验证 learning/ 目录下存在 README.md（执行摘要）
   - 验证 learning/skills/ 下的 Python 文件语法合法（`python3 -m py_compile`）
   - 输出：`PASS` 或 `FAIL: <reason>`，退出码 0/1
4. 所有 check 命令支持 `--json` flag，以 JSON 格式输出结果（供 skill 解析）
5. 实现 `sense tools doing_check` 的 zombie task 检测：读 tasks.json，将 running 状态的 task 重置为 pending（幂等恢复）

# 测试方法
1. Python 脚本：创建合法的 plan 目录，运行 `sense tools plan_check job_1`，验证退出码为 0 且输出 PASS
2. Python 脚本：创建缺少 `# 关键结果` section 的 task.md，运行 plan_check，验证退出码为 1 且输出包含 FAIL 原因
3. Python 脚本：创建含 zombie task（status=running）的 tasks.json，运行 `sense tools doing_check job_1`，验证退出码为 1
4. Python 脚本：创建含语法错误 Python 文件的 learning/skills/，运行 learning_check，验证退出码为 1
5. Python 脚本：运行 `sense tools plan_check job_1 --json`，验证输出为合法 JSON（`{"pass": true/false, "errors": [...]}`）
