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
