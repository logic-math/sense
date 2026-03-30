# OKR — sense 项目

## Objective
构建 sense-ai-loop：一个人类帮助 AI 成长的循环。以结构化文档为输入，驱动 AI 自动完成软件开发任务，并将经验沉淀回项目上下文（wiki、skills、OKR、SPEC）。

## Key Results

### KR1：sense CLI 完整实现（已完成 job_1）
- [x] `sense init`：初始化 `.sense/` 工作空间
- [x] `sense doing dag <job_id>`：解析 plan/*.md → tasks.json
- [x] `sense doing next_task <job_id>`：返回下一个可执行 task
- [x] `sense doing update_task <job_id> <task_id> <status>`：更新任务状态
- [x] `sense doing list <job_id>`：展示任务状态表格
- [x] `sense job list`：列出所有 job
- [x] `sense tools gen_prompt <phase> <job_id> [task_id]`：生成各阶段 prompt
- [x] `sense tools plan_check / doing_check / learning_check`：质量门禁
- [x] `sense learning merge <job_id>`：合并 learning 产物到 .sense/

### KR2：sense-ai-loop skill 完整实现（已完成 job_1）
- [x] `skills/sense-ai-loop/SKILL.md`：主控循环
- [x] `skills/sense-ai-loop/skills/plan.md`：plan sub-agent 规则
- [x] `skills/sense-ai-loop/skills/doing.md`：doing sub-agent 规则
- [x] `skills/sense-ai-loop/skills/learning.md`：learning sub-agent 规则

### KR3：自举验证（已完成 job_1）
- [x] `tests/mock_agent/mock_agent.py`：模拟 sub-agent 文件系统操作
- [x] `tests/integration_test.sh`：端到端集成测试
- [x] `scripts/build.sh`：编译脚本

### KR4：后续迭代目标（job_2 部分完成）
- [x] parser 支持逗号分隔依赖（job_2/task1）
- [x] gen_prompt 路径规范化（job_2/task4）
- [x] learning_check 路径修复（job_2/task4）
- [x] learning prompt job_summary 注入（job_2/task3）
- [ ] review 阶段（SPEC 合规性检查）
- [ ] prompt 模板语言中文化
- [ ] gen_prompt learning 注入 git log
- [ ] sense CLI 支持从 sense-express 文档直接解析生成 plan
- [ ] 与 sense-human-loop 深度集成
