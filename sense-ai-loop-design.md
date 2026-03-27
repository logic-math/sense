# sense-ai-loop 设计文档

> **文档类型：** SENSE 思考记录
> **创建时间：** 2026-03-27
> **思考主体：** sunquan
> **适用场景：** 作为 sense-ai-loop 开发的上下文，供人和 AI 共读

---

## 1. 澄清问题（Subject）

**现状**

已有 sense-human-loop：一个 AI 倒逼人类思考、帮助人类成长的循环。它通过 SENSE 方法论引导用户完成深度思考，最终由 sense-express 产出结构化文档。

已有 rick CLI：一个基于上下文优先理念的 AI 编程框架，实现了 plan → doing → learning 三步循环，内部通过 `exec.Command("claude", promptFile)` 启动交互式或后台 Claude 子进程执行任务。

**期望**

构建 sense-ai-loop：一个人类帮助 AI 成长的循环。以 sense-express 产出的结构化文档为输入，驱动 AI 自动完成软件开发任务，并将经验沉淀回项目上下文（wiki、skills、OKR、SPEC）。

sense CLI 是这个循环的核心工具。sense skill（SKILL.md）是这个工具的使用说明书，告诉 Claude Code 何时以及如何调用它。

**差距**

1. rick 的 plan 和 learning 使用交互式 Claude 子进程，无法作为 sub-agent 在 Claude Code 内部调用
2. rick 的上下文组织在 `.rick/` 下，与 sense 生态不统一
3. rick 没有 review 阶段（SPEC 合规性检查）
4. rick 没有将 skills 作为项目交付产物的机制
5. sense-express 文档与 rick task.md 之间存在语义差距：前者描述"为什么和怎么做"，后者描述"落地所需的所有细节"

---

## 2. 假设视角（Perspective）

**核心假设**

sense CLI 本身运行在 Claude Code 交互窗口中，不需要启动 Claude 子进程——它只负责管理上下文、生成 prompt、验证产物；真正的 AI 执行由 Claude Code 的 Agent tool（sub-agent）完成。

**假设依据**

- sense-human-loop 已经在 Claude Code 中运行，skill 可以调用 Agent tool 启动 sub-agent
- sub-agent 是后台非交互式执行，和 rick 的 `--dangerously-skip-permissions` 模式等价，但不需要启动子进程
- 用户如果需要修改 plan，直接在 Claude Code 交互窗口对话，然后重新触发 plan sub-agent 即可

**融贯性检验**

- 自洽：sense CLI 只做文件管理 + prompt 生成 + check，不调用 claude 命令，内部逻辑自洽
- 他洽：与 Claude Code skill 机制完全吻合，Agent tool 就是为这种场景设计的
- 续洽：未来 sense CLI 可以独立于 Claude Code 使用（只要有 claude 命令），但在 Claude Code 内使用时走 sub-agent 路径更高效

---

## 3. 矛盾判断（Judgment）

**系统中的主要矛盾**

"AI 执行能力"和"人类意图准确传达"之间的矛盾：AI 执行能力越强，越需要精确的上下文；但上下文越精确，越需要人类投入更多时间整理。

**矛盾分析**

- 影响范围：每一次 job 执行都受此矛盾影响
- 影响深度：这个矛盾决定了 plan 阶段的设计——plan 必须把 sense-express 文档（"为什么/怎么做"）转化为 task DAG（"落地细节"），填补语义差距

**选择的控制手段**

以"上下文积累"为控制手段：每次 job 完成后，learning 阶段将变更上下文合并到项目级（OKR、SPEC、wiki、skills），使下一次 job 的 AI 执行精度持续提升。项目本身就是记忆系统。

**排除的选项**

- 排除"人工编写 task.md"：违背自动化目标
- 排除"直接用 sense-express 文档驱动 doing"：语义差距太大，AI 无法直接从"为什么"推导出"落地细节"
- 排除"保留 rick 的交互式模式"：无法作为 sub-agent 调用

---

## 4. 解决方法（Reverse）

**方案描述**

用 Go 实现 sense CLI（借鉴 rick 代码），上下文组织在 `.sense/` 目录下。sense skill 告诉 Claude Code 如何驱动 sense CLI。plan 和 learning 改为非交互式 sub-agent 执行。

**目录结构**

```
.sense/
├── OKR.md                    # 项目目标与规划（全局，跨 job 持续更新）
├── SPEC.md                   # coding 规范（每次 doing 必须遵循）
├── wiki/                     # 项目知识库（learning 持续更新）
├── skills/                   # Claude Code skill 描述文件（何时/如何使用工具）
└── jobs/
    └── job_1/
        ├── README.md         # learning 产出的工作摘要（事无巨细）
        ├── prompts/          # 所有阶段的 prompt 文件（审查用）
        │   ├── plan.md
        │   ├── task1_test1.md
        │   ├── task1_doing1.md
        │   ├── task1_review1.md
        │   ├── task1_debug1.md
        │   └── learning.md
        ├── plan/
        │   ├── task1.md
        │   └── task2.md
        └── doing/
            ├── tasks.json    # DAG 调度元信息
            └── task1/
                ├── test1.py
                ├── doing1.md     # sub-agent worklog
                ├── review1.md
                ├── debug1.md
                └── doing2.md    # 第二次执行（如有重试）
```

实际工具脚本（Python）作为项目交付产物放在项目代码目录（如 `scripts/`），`.sense/skills/` 只存 Claude Code skill 描述文件。

**CLI 命令树**

```
sense plan <doc>               # 解析 sense-express 文档，生成 task DAG
sense doing dag <job_id>       # 解析 plan/*.md → tasks.json
sense doing next_task <job_id> # 返回下一个待执行 task ID（或 None）
sense doing <job_id>           # 主循环入口（skill 驱动）
sense learning <job_id>        # 触发 learning 阶段
sense tools plan_check <job_id>
sense tools doing_check <job_id>
sense tools learning_check <job_id>
```

**doing 主循环（skill 驱动）**

```
sense doing dag job_1          # 生成 tasks.json
loop:
  taskID = sense doing next_task job_1
  if taskID == None: break

  # 红阶段：生成测试
  subagent(test_prompt)        → job_1/doing/task1/test1.py
                                  job_1/prompts/task1_test1.md

  # 绿阶段：实现
  subagent(doing_prompt)       → worklog: job_1/doing/task1/doing1.md
                                  prompt:  job_1/prompts/task1_doing1.md

  # review：SPEC 合规检查
  subagent(review_prompt)      → job_1/doing/task1/review1.md
                                  job_1/prompts/task1_review1.md

  # 运行测试
  run test1.py
  if fail:
    subagent(debug_prompt)     → job_1/doing/task1/debug1.md
    subagent(review_prompt)    → job_1/doing/task1/review2.md
    run test1.py
    ...until pass

  git commit                   # task 粒度提交，支持回滚

# learning 阶段
subagent(summary_prompt)       → job_1/README.md（全量变更摘要）
subagent(wiki_prompt)          → .sense/wiki/ diff + changelog
subagent(skills_prompt)        → 项目 scripts/ 工具脚本
                                  .sense/skills/ 使用说明
```

**上下文压缩容错**

tasks.json 是调度元信息，记录每个 task 的状态。当 Claude Code 上下文压缩后，skill 从 tasks.json 读取当前状态，从断点处继续执行。项目本身就是记忆系统，不依赖对话历史。

**关键路径**

1. 实现 sense CLI（Go）：workspace 管理、prompt 生成、check 逻辑、DAG 调度
2. 编写 sense-ai-loop skill（SKILL.md）：驱动 plan → doing → learning 完整循环
3. 编写子 skill 文件：plan/doing/learning 各自的执行规则

---

## 5. 过程批判（Critique）

**核心假设清单**

| 假设 | 如果不成立，结论会…… |
|------|---------------------|
| sense CLI 运行在 Claude Code 中，可以通过 Agent tool 调用 sub-agent | 需要退回到 rick 的 `exec.Command("claude")` 模式，但 plan/learning 仍可非交互式 |
| sense-express 文档结构足够稳定，plan sub-agent 可以可靠解析 | 需要在 plan prompt 中加入更多解析容错逻辑 |
| tasks.json 足以作为上下文压缩后的恢复锚点 | 需要在 tasks.json 中记录更多状态信息 |
| learning 阶段的 skills sub-agent 能识别出值得抽象为工具的功能 | skills 产出质量下降，需要人工干预 |
| Python 测试脚本输出 JSON 格式结果，sense CLI 可以可靠解析 | 需要在 test prompt 中强制规定输出格式 |

**逻辑漏洞**

- review 阶段的 SPEC 合规检查依赖 git diff，需要确保每次 doing sub-agent 执行后有未提交的变更可供检查（不能提前 commit）
- doing 和 review 可能多次执行，文件命名需要 sense CLI 维护计数器（doing1.md, doing2.md...），这个计数器状态需要持久化到 tasks.json 中

**良质确认**

这个方案符合核心目标：让 AI 在人类思考清晰后自动完成软件开发，并将经验持续沉淀回项目。整个项目成为一个自我成长的验证环境——包含交付产物、技能工具、运行原理与控制方法、变更历史。这正是"人类帮助 AI 成长"的循环。

**下一步行动**

- [ ] 实现 sense CLI（Go），参考 rick 的 workspace、parser、executor 模块
- [ ] 实现 `sense doing dag` 和 `sense doing next_task` 子命令
- [ ] 实现 `sense tools plan_check / doing_check / learning_check`
- [ ] 编写 plan prompt 模板（解析 sense-express 文档 → OKR + SPEC + task DAG）
- [ ] 编写 doing prompt 模板（test / doing / review / debug 四种）
- [ ] 编写 learning prompt 模板（summary / wiki / skills 三种）
- [ ] 编写 sense-ai-loop SKILL.md（主控循环）
- [ ] 验证：用 sense-ai-loop 开发 sense CLI 本身（自举）
