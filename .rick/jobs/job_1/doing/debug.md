## task1: 初始化 sense 项目结构（Go module + workspace 模块）

**分析过程 (Analysis)**:
- 项目目录 /Users/sunquan/ai_coding/CODING/sense 已存在，但尚无 Go 代码
- 测试脚本 .rick/jobs/job_1/doing/tests/task1.py 已由 rick 框架预先生成
- 测试脚本通过写入临时 Go 测试文件来验证 workspace.NextJobID 和 parser.ParseTaskFile
- 测试中 NextJobID(dir) 传入的 dir 是 `.sense/` 目录本身（非项目根目录），因此函数应查找 `<root>/jobs/` 而非 `<root>/.sense/jobs/`

**实现步骤 (Implementation)**:
1. `go mod init github.com/sunquan/sense` 初始化 Go module
2. 创建目录结构：cmd/sense/、internal/cmd/、internal/workspace/、internal/parser/、bin/
3. 实现 internal/cmd/root.go：cobra 根命令，版本号 0.1.0
4. 实现 cmd/sense/main.go：调用 cmd.Execute()
5. 实现 internal/workspace/workspace.go：Init()、GetSenseDir()、NextJobID()、GetJobPlanDir()、GetJobDoingDir()、GetJobLearningDir()
6. 实现 internal/cmd/init.go：sense init 子命令，调用 workspace.Init()
7. 实现 internal/parser/task.go：ParseTaskFile() 解析 task.md 五个 section
8. `go get github.com/spf13/cobra@latest` 添加 cobra 依赖
9. `go build -o bin/sense ./cmd/sense/...` 编译成功

**遇到的问题 (Issues)**:
- NextJobID 参数语义问题：初始实现中 root 为项目根目录，查找 `<root>/.sense/jobs/`；但测试脚本传入的是 `.sense/` 目录，期望查找 `<root>/jobs/`。修复：将 NextJobID 的 root 语义改为 `.sense/` 目录，查找 `<root>/jobs/`。

**验证结果 (Verification)**:
- 测试命令：`python3 .rick/jobs/job_1/doing/tests/task1.py`
- 测试输出：
  ```
  {"pass": true, "errors": []}
  ```
- 结论：✅ 通过

## task2: 实现 DAG 调度核心（dag + topological + tasks_json）

**分析过程 (Analysis)**:
- 已有 internal/parser/task.go 提供 ParseTaskFile()，返回含 Dependencies、Name 等字段的 Task 结构
- 已有 internal/workspace/workspace.go 提供 GetJobPlanDir/GetJobDoingDir，接受项目根目录
- 测试脚本在 tmpdir 下创建 .sense/jobs/job_1/plan/*.md，运行 `sense doing dag job_1`，cwd=tmpdir
- 需要新建 internal/executor/ 包：dag.go、topological.go、tasks_json.go
- 需要新建 internal/cmd/doing.go 注册 doing dag 和 doing next_task 子命令

**实现步骤 (Implementation)**:
1. 创建 internal/executor/dag.go：定义 Node、DAG、TaskEntry 结构体，BuildDAG() 验证依赖存在并检测循环
2. 创建 internal/executor/topological.go：Kahn 算法拓扑排序，循环依赖时返回 error
3. 创建 internal/executor/tasks_json.go：TasksJSON/TaskRecord 结构体，Load/Save/NewTasksJSON/UpdateStatus/UpdateCommit/NextTask 方法
4. 创建 internal/cmd/doing.go：doing 父命令 + dag 子命令（读 plan/*.md → BuildDAG → TopologicalSort → NewTasksJSON → Save）+ next_task 子命令（Load → NextTask → 输出 task_id 或 NONE）
5. `go build -o bin/sense ./cmd/sense/...` 编译成功

**遇到的问题 (Issues)**:
- 无

**验证结果 (Verification)**:
- 测试命令：`python3 .rick/jobs/job_1/doing/tests/task2.py`
- 测试输出：
  ```
  {"pass": true, "errors": []}
  ```
- 结论：✅ 通过

## task3: 实现 prompt 模板系统（plan/doing/learning/review/test prompt 生成）

**分析过程 (Analysis)**:
- 已有 internal/workspace/workspace.go 提供 GetSenseDir/GetJobPlanDir/GetJobDoingDir
- 已有 internal/parser/task.go 提供 ParseTaskFile()
- 测试脚本在 tmpdir 下创建 .sense/{OKR.md,SPEC.md,wiki/,skills/,jobs/job_1/plan/task1.md}
- 运行 `sense tools gen_prompt plan job_1`，验证生成的 prompt 包含 OKR/SPEC/wiki/skills 内容
- 运行 `sense tools gen_prompt doing job_1 task1`，验证包含 task 目标和测试方法
- 运行 `sense tools gen_prompt test job_1 task1`，验证包含测试脚本路径占位符
- 生成文件输出到 `prompts/` 目录

**实现步骤 (Implementation)**:
1. 创建 internal/prompt/context.go：LoadContext() 读取 OKR.md、SPEC.md、wiki/、skills/；WikiContent()/SkillsContent() 拼接内容
2. 创建 internal/prompt/templates/{plan,doing,test,review,learning}.md：Markdown 模板，使用 {{variable}} 占位符
3. 创建 internal/prompt/builder.go：使用 //go:embed 嵌入模板文件；Build() 进行字符串替换
4. 创建 internal/cmd/tools.go：tools 父命令 + gen_prompt 子命令，加载上下文、解析 task 文件、渲染模板、写入 prompts/ 目录
5. `go build -o bin/sense ./cmd/sense/...` 编译成功

**遇到的问题 (Issues)**:
- 无

**验证结果 (Verification)**:
- 测试命令：`python3 .rick/jobs/job_1/doing/tests/task3.py`
- 测试输出：
  ```
  {"pass": true, "errors": []}
  ```
- 结论：✅ 通过

## task4: 实现 tools check 命令（plan_check / doing_check / learning_check）

**分析过程 (Analysis)**:
- 已有 internal/cmd/tools.go 提供 gen_prompt 子命令，在此基础上扩展三个 check 子命令
- 已有 internal/executor/dag.go 提供 BuildDAG() 可复用做循环检测
- 已有 internal/executor/tasks_json.go 提供 Load() 和 StatusRunning 常量
- 已有 internal/workspace/workspace.go 提供 GetJobPlanDir/DoingDir/LearningDir
- 测试脚本验证：plan_check PASS/FAIL、doing_check zombie task 检测、learning_check Python 语法检查、--json flag

**实现步骤 (Implementation)**:
1. 在 tools.go 添加 checkResult 结构体（Pass bool + Errors []string），实现 output(jsonMode) 和 exitCode()
2. 实现 planCheckCmd：扫描 plan/*.md，检查五个必要 section，用 BuildDAG 检测循环依赖
3. 实现 doingCheckCmd：Load tasks.json，检测 status=running 的 zombie task
4. 实现 learningCheckCmd：验证 README.md 存在，对 skills/*.py 运行 python3 -m py_compile 检查语法
5. 为三个命令注册 --json flag，在 init() 中添加到 toolsCmd
6. `go build -o bin/sense ./cmd/sense/...` 编译成功

**遇到的问题 (Issues)**:
- 无

**验证结果 (Verification)**:
- 测试命令：`python3 .rick/jobs/job_1/doing/tests/task4.py`
- 测试输出：
  ```
  {"pass": true, "errors": []}
  ```
- 结论：✅ 通过
