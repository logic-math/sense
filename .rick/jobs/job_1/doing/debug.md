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

## task5: 实现 sense doing update_task 和 learning merge 命令

**分析过程 (Analysis)**:
- 已有 internal/executor/tasks_json.go 提供 Load/Save/UpdateStatus/UpdateCommit，但 Save 非原子写入
- 已有 internal/cmd/doing.go 提供 dag/next_task 子命令，在此基础上扩展 update_task/list
- 已有 internal/workspace/workspace.go 提供 GetJobLearningDir/GetSenseDir/ListJobIDs
- 需要新建 internal/cmd/learning.go（learning merge）和 internal/cmd/job.go（job list）
- 测试脚本验证：update_task 更新状态+commit_hash、幂等性、learning merge 文件复制、doing list 表格输出、不存在 task_id 返回非零

**实现步骤 (Implementation)**:
1. 修改 tasks_json.go Save() 为原子写入（先写 .tmp 再 rename）
2. 在 tasks_json.go 中添加 UpdateAttempts() 方法
3. 在 doing.go 中添加 doingUpdateTaskCmd（支持 --commit/--attempts flag）和 doingListCmd（表格输出）
4. 新建 internal/cmd/learning.go：learning 父命令 + merge 子命令（合并 wiki/skills 目录，支持 OKR.md/SPEC.md）
5. 新建 internal/cmd/job.go：job 父命令 + list 子命令（读各 job 的 tasks.json 推断状态）
6. `go build -o bin/sense ./cmd/sense/...` 编译成功

**遇到的问题 (Issues)**:
- 无

**验证结果 (Verification)**:
- 测试命令：`python3 .rick/jobs/job_1/doing/tests/task5.py`
- 测试输出：
  ```
  {"pass": true, "errors": []}
  ```
- 结论：✅ 通过

## task6: 编写 sense-ai-loop SKILL.md（主控循环 + plan/doing/learning 子 skill）

**分析过程 (Analysis)**:
- 阅读了 sense-ai-loop-design.md，理解了三阶段循环（plan → doing → learning）的完整设计
- 阅读了 skills/sense-human-loop/SKILL.md 作为 skill 格式参考
- 阅读了 internal/prompt/templates/ 下的所有模板，理解了 sense CLI 的命令体系
- 阅读了 install 脚本，了解 skill 注册机制（自动扫描 skills/*/SKILL.md，无需手动注册）

**实现步骤 (Implementation)**:
1. 创建 skills/sense-ai-loop/ 目录和 skills/sense-ai-loop/skills/ 子目录
2. 创建 skills/sense-ai-loop/SKILL.md：主控 skill，含触发条件、三阶段流程、doing 主循环伪代码、上下文恢复机制、失败处理策略
3. 创建 skills/sense-ai-loop/skills/plan.md：plan sub-agent 规则，含输入规范、task*.md 格式要求、解析 sense-express 文档的映射规则
4. 创建 skills/sense-ai-loop/skills/doing.md：doing sub-agent 规则，含输入规范、五步执行流程（分析→实现→测试→工作日志→提交）
5. 创建 skills/sense-ai-loop/skills/learning.md：learning sub-agent 规则，含三个产出（README.md + wiki + skills）的详细规范
6. 更新 install 脚本帮助信息，添加 sense-ai-loop 说明

**遇到的问题 (Issues)**:
- 无

**验证结果 (Verification)**:
- 测试命令：`python3 .rick/jobs/job_1/doing/tests/task6.py`
- 测试输出：
  ```
  {"pass": true, "errors": []}
  ```
- 结论：✅ 通过

## task7: 编写 mock_agent.py 和集成测试（自举验证 sense CLI）

**分析过程 (Analysis)**:
- 阅读了 task7.py 测试脚本，理解了7个测试要求：mock_agent.py 存在 + --self-test 通过、integration_test.sh 存在 + 退出码0 + 覆盖 dag/next_task/NONE、plan_check 对缺失 section 返回 FAIL、doing_check 对 zombie task 返回 FAIL 并支持自动恢复
- 阅读了 internal/parser/task.go，发现依赖关系行直接存储原始文本（不去掉 "- " 前缀），因此 plan 文件的依赖关系必须直接写 taskID 而不是 "- taskID"
- 阅读了 internal/cmd/tools.go，确认 doing_check 对任何 status=running 的任务都报告 zombie，plan_check 检查五个必要 section
- 阅读了 internal/workspace/workspace.go，确认路径格式：.sense/jobs/{jobID}/plan、doing、learning

**实现步骤 (Implementation)**:
1. 创建 tests/mock_agent/mock_agent.py：7 个场景（plan_success/missing_section/circular_dep/doing_success/test_success/test_fail/learning_success），通过 MOCK_SCENARIO 环境变量切换，支持 --self-test 模式
2. 创建 tests/integration_test.sh：10 个端到端测试，覆盖 sense init → doing dag → next_task 调度循环（task1→task2→NONE）→ plan_check PASS/FAIL → doing_check zombie 检测和自动恢复 → learning merge
3. 创建 scripts/build.sh：编译 sense 到 bin/sense

**遇到的问题 (Issues)**:
- 依赖格式问题：初始实现中 plan 文件依赖写成 "- task1"，但 parser 直接存储原始行，导致 DAG 报错 "depends on unknown task '- task1'"。修复：改为直接写 "task1"（与项目现有 plan 文件格式一致）
- integration_test.sh 中 SENSE_BIN 路径问题：初始用 `$(dirname "$0")/../bin/sense` 是相对路径，cd 到 tmpdir 后失效。修复：改为 `$(cd "$(dirname "$0")/.." && pwd)/bin/sense` 绝对路径

**验证结果 (Verification)**:
- 测试命令：`python3 tests/mock_agent/mock_agent.py --self-test && bash tests/integration_test.sh && python3 .rick/jobs/job_1/doing/tests/task7.py`
- 测试输出：
  ```
  OK: all self-tests passed
  PASS: sense init creates .sense directory structure
  PASS: sense doing dag generates tasks.json
  PASS: sense doing next_task returns task1 first
  PASS: sense doing next_task returns task2 after task1 completes
  PASS: sense doing next_task returns NONE when all tasks done
  PASS: sense tools plan_check PASS for valid plan
  PASS: sense tools plan_check FAIL for plan_missing_section
  PASS: sense tools doing_check FAIL for zombie task
  PASS: sense tools doing_check PASS after zombie reset to pending
  PASS: sense learning merge copies wiki and skills files
  Results: 10 passed, 0 failed
  {"pass": true, "errors": []}
  ```
- 结论：✅ 通过
