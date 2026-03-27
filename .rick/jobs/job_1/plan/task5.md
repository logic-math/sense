# 依赖关系
task2, task3

# 任务名称
实现 sense doing update_task 和 learning merge 命令（任务状态管理 + learning 合并）

# 任务目标
实现 `sense doing update_task <job_id> <task_id> <status> [--commit <hash>]` 命令（供 skill 更新任务状态）和 `sense learning merge <job_id>` 命令（将 learning 产物合并到 `.sense/` 项目上下文）。这两个命令是 doing 循环和 learning 阶段的收尾动作。

# 关键结果
1. 实现 `sense doing update_task <job_id> <task_id> <status>` 命令：
   - 读取 tasks.json，更新指定 task 的 status（pending/running/success/failed）
   - 支持 `--commit <hash>` flag，记录 commit hash
   - 支持 `--attempts <n>` flag，更新重试次数
   - 原子写入（先写临时文件，再 rename）
2. 实现 `sense learning merge <job_id>` 命令：
   - 将 `learning/wiki/` 下的文件合并（覆盖/追加）到 `.sense/wiki/`
   - 将 `learning/skills/` 下的文件合并到 `.sense/skills/`
   - 如果 learning 产出了新的 OKR.md/SPEC.md，提示用户确认后更新 `.sense/OKR.md`/`.sense/SPEC.md`
   - 合并完成后输出合并摘要（新增/更新了哪些文件）
3. 实现 `sense doing list <job_id>` 命令：以表格形式展示 tasks.json 中所有 task 的状态
4. 实现 `sense job list` 命令：列出所有 job 及其状态（通过读取各 job 的 tasks.json 推断）
5. 所有写操作均支持幂等（重复执行结果相同）

# 测试方法
1. Python 脚本：创建 tasks.json（task1=pending），运行 `sense doing update_task job_1 task1 success --commit abc1234`，验证 tasks.json 中 task1.status=success 且 commit_hash=abc1234
2. Python 脚本：运行两次相同的 update_task 命令，验证结果幂等（第二次不报错，状态保持一致）
3. Python 脚本：创建 `learning/wiki/arch.md` 和 `learning/skills/check.py`，运行 `sense learning merge job_1`，验证文件被复制到 `.sense/wiki/` 和 `.sense/skills/`
4. Python 脚本：运行 `sense doing list job_1`，验证输出包含 task ID 和状态列
5. Python 脚本：验证 `sense doing update_task` 对不存在的 task_id 返回非零退出码和错误信息
