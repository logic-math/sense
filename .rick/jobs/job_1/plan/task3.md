# 依赖关系
task1

# 任务名称
实现 prompt 模板系统（plan/doing/learning/review/test prompt 生成）

# 任务目标
实现 `internal/prompt/` 模块，负责生成各阶段的 prompt 文件。prompt 是 sense-ai-loop skill 传给 sub-agent 的核心输入，内容包含：项目上下文（OKR、SPEC、wiki、skills）+ 阶段指令 + 任务信息。

# 关键结果
1. 实现 `internal/prompt/context.go`：ContextManager，加载 OKR.md、SPEC.md、wiki/、skills/ 内容
2. 实现 `internal/prompt/templates/` 目录，包含以下 Markdown 模板文件（嵌入到二进制）：
   - `plan.md`：plan prompt 模板（输入：用户需求/sense-express 文档路径；输出：task*.md 到 plan 目录）
   - `test.md`：test prompt 模板（输入：task 信息；输出：Python 测试脚本到 doing/taskN/ 目录）
   - `doing.md`：doing prompt 模板（输入：task 信息 + 测试脚本路径；输出：实现代码 + doing worklog）
   - `review.md`：review prompt 模板（输入：task 信息 + git diff；输出：review.md 到 doing/taskN/）
   - `learning.md`：learning prompt 模板（输入：job 执行摘要；输出：README.md + wiki diff + skills）
3. 实现 `internal/prompt/builder.go`：模板变量替换（`{{variable}}` 语法）
4. 实现 `sense tools gen_prompt <phase> <job_id> [task_id]` 子命令：生成指定阶段的 prompt 文件到 `prompts/` 目录（供审查）
5. prompt 文件中自动注入 OKR、SPEC、wiki、skills 上下文（从 `.sense/` 读取）

# 测试方法
1. Python 脚本：创建 `.sense/OKR.md` 和 `.sense/SPEC.md`，运行 `sense tools gen_prompt plan job_1`，验证生成的 prompt 文件包含 OKR 和 SPEC 内容
2. Python 脚本：验证 `sense tools gen_prompt doing job_1 task1` 生成的 doing prompt 包含 task 的目标和测试方法
3. Python 脚本：验证 `sense tools gen_prompt test job_1 task1` 生成的 test prompt 包含测试脚本路径占位符
4. Python 脚本：验证 `.sense/wiki/` 和 `.sense/skills/` 目录中的文件内容被正确注入到 prompt 中
5. `go build ./...` 编译成功（模板文件通过 `//go:embed` 嵌入）
