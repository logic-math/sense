# sense 项目架构

## 项目定位

sense 是一个基于 SENSE 方法论的 AI 编程框架，核心是 **sense-ai-loop**：人类通过 sense-human-loop 想清楚需求，AI 通过 sense-ai-loop 自动完成软件开发，经验沉淀回项目上下文形成闭环。

```
人类思考（sense-human-loop）
    ↓ sense-express 文档
AI 编程（sense-ai-loop）
    ↓ 代码 + 知识
项目上下文（.sense/wiki、skills、OKR、SPEC）
    ↑ 下次循环输入
```

## 系统组成

### sense CLI（Go）
核心工具，负责工作空间管理、prompt 生成、质量检查、DAG 调度。

**模块结构：**
```
cmd/sense/main.go              # 入口
internal/
  cmd/                         # cobra 子命令
    root.go                    # 根命令（version 0.1.0）
    init.go                    # sense init
    doing.go                   # sense doing dag/next_task/update_task/list
    job.go                     # sense job list
    learning.go                # sense learning merge
    tools.go                   # sense tools gen_prompt/plan_check/doing_check/learning_check
  workspace/workspace.go       # .sense/ 目录管理
  parser/task.go               # task.md 解析
  executor/
    dag.go                     # DAG 构建
    topological.go             # Kahn 拓扑排序
    tasks_json.go              # tasks.json 读写
  prompt/
    context.go                 # 项目上下文加载
    builder.go                 # 模板渲染（//go:embed）
    templates/                 # plan/doing/test/review/learning.md 模板
```

### sense-ai-loop skill（Claude Code）
告诉 Claude Code 如何驱动 sense CLI 完成 plan → doing → learning 循环。

```
skills/
  sense-ai-loop/
    SKILL.md                   # 主控循环（触发词：sense loop、用 sense 实现）
    skills/
      plan.md                  # plan sub-agent 规则
      doing.md                 # doing sub-agent 规则
      learning.md              # learning sub-agent 规则
  sense-human-loop/
    SKILL.md                   # 深度思考循环
    skills/
      sense-think/SKILL.md
      sense-learn/SKILL.md
      sense-express/SKILL.md
```

### .sense/ 工作空间
```
.sense/
  OKR.md                       # 项目目标（跨 job 持续更新）
  SPEC.md                      # 编码规范（每次 doing 必须遵循）
  wiki/                        # 项目知识库（learning 持续更新）
  skills/                      # 项目工具描述文件
  jobs/
    job_1/
      plan/                    # task*.md + tasks.json（plan 阶段产出）
      doing/
        tasks.json             # DAG 调度元信息（唯一状态锚点）
        tests/                 # Python 测试脚本
```

## 核心设计决策

### 1. sense CLI 不调用 claude 命令
与前身 rick 不同，sense CLI 只做文件管理 + prompt 生成 + check，不启动 claude 子进程。真正的 AI 执行由 Claude Code 的 Agent tool（sub-agent）完成。

### 2. tasks.json 是唯一状态锚点
当 Claude Code 上下文压缩后，通过 `sense doing next_task` 读取 tasks.json 恢复执行进度，不依赖对话历史。

### 3. 项目本身就是记忆系统
每次 job 完成后，learning 阶段将变更合并到 .sense/wiki/ 和 .sense/skills/，使下一次 job 的 AI 执行精度持续提升。

### 4. 原子写入
tasks.json 写入通过"先写 .tmp，再 rename"保证原子性，防止进程中断导致数据损坏。
