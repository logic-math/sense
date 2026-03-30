# 依赖关系
（无）

# 任务名称
初始化 sense 项目结构（Go module + workspace 模块）

# 任务目标
建立 sense CLI 的项目骨架：Go module、cobra 根命令、workspace 管理模块（`.sense/` 目录结构初始化、路径查询、job 管理）。这是所有后续模块的基础。

# 关键结果
1. 创建 `go.mod`（module: `github.com/sunquan/sense`，依赖 cobra）
2. 实现 `cmd/sense/main.go` + `internal/cmd/root.go`，`sense --version` 可运行
3. 实现 `internal/workspace/` 模块：`Init()`、`GetSenseDir()`、`NextJobID()`、`GetJobPlanDir()`、`GetJobDoingDir()`、`GetJobLearningDir()` 等路径函数
4. 实现 `sense init` 子命令，在当前目录创建 `.sense/` 目录结构（OKR.md、SPEC.md、wiki/、skills/、jobs/）
5. 实现 `internal/parser/` 模块：解析 task.md 格式（依赖关系、任务名称、任务目标、关键结果、测试方法）

# 测试方法
1. `go build ./...` 编译成功，无报错
2. `./bin/sense --version` 输出版本号
3. `./bin/sense init` 在临时目录创建 `.sense/` 结构，Python 脚本验证目录和文件存在
4. Python 脚本验证 `workspace.NextJobID()` 在空 jobs 目录返回 `job_1`，在已有 `job_1` 时返回 `job_2`
5. Python 脚本验证 parser 能正确解析 task.md 的五个 section（依赖关系、任务名称、任务目标、关键结果、测试方法），并验证 `（无）` 表示无依赖
