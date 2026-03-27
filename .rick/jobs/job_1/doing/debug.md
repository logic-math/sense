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
