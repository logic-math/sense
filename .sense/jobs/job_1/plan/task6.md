# 依赖关系
task3, task4, task5

# 任务名称
编写 sense-ai-loop SKILL.md（主控循环 + plan/doing/learning 子 skill）

# 任务目标
编写 sense-ai-loop skill 的所有 SKILL.md 文件，使 Claude Code 能够通过 Agent tool 驱动 plan → doing → learning 完整循环。这是 sense 生态的 AI 编程入口，也是 sense CLI 的使用说明书。

# 关键结果
1. 创建 `skills/sense-ai-loop/SKILL.md`：主控 skill，定义触发条件（`sense loop`、`用 sense 实现`、`ai loop`）和完整循环流程
2. 主控 skill 的 doing 循环逻辑：
   - 调用 `sense doing dag` 生成 tasks.json
   - 循环：调用 `sense doing next_task` → 启动 test sub-agent → 启动 doing sub-agent → 运行测试 → 失败则 debug sub-agent → git commit → 更新 task 状态
   - 所有循环完成后调用 `sense tools doing_check` 验证
3. 创建 `skills/sense-ai-loop/skills/plan.md`：plan sub-agent 的执行规则（如何解析输入文档、生成 task*.md）
4. 创建 `skills/sense-ai-loop/skills/doing.md`：doing sub-agent 的执行规则（如何实现任务、写 worklog）
5. 创建 `skills/sense-ai-loop/skills/learning.md`：learning sub-agent 的执行规则（如何生成 README.md、wiki diff、skills）
6. 在 `install` 脚本中注册 `sense-ai-loop` skill

# 测试方法
1. 验证 SKILL.md 的 frontmatter 格式合法（name、description 字段存在）
2. 验证主控 skill 中包含 `sense doing dag`、`sense doing next_task`、`sense tools doing_check` 等关键命令引用
3. 验证 plan/doing/learning 子 skill 文件存在且包含明确的输入/输出规范
4. 运行 `./install --list` 验证 `sense-ai-loop` 出现在可安装列表中
5. 手动触发验证：在 Claude Code 中输入 `sense loop`，验证主控 skill 被正确加载（通过检查 skill 是否出现在系统提示中）
