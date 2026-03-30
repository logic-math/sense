# sense CLI 命令参考

## 安装

```bash
# 编译
bash scripts/build.sh        # 输出到 bin/sense

# 安装到 PATH
./install                    # 安装 CLI 到 ~/.local/bin/sense，安装 skills 到 ~/.claude/skills/
```

## 工作空间管理

### `sense init`
在当前目录初始化 `.sense/` 工作空间。

```bash
sense init
```

**创建结构：**
```
.sense/
  OKR.md
  SPEC.md
  wiki/
  skills/
  jobs/
```

**注意：** sense CLI 使用 `os.Getwd()` 作为项目根目录，所有命令必须在包含 `.sense/` 的目录下运行。

---

## Job 管理

### `sense job list`
列出所有 job 及其状态。

```bash
sense job list
```

**输出示例：**
```
JOB_ID       STATUS      TASKS
--------------------------------------------------
job_1        success     7/7 done
job_2        success     5/5 done
```

**状态推断逻辑：** 有 failed → failed；有 running → running；有 pending → pending；否则 → success。

---

## Doing 阶段

### `sense doing dag <job_id>`
解析 `.sense/jobs/{job_id}/plan/*.md`，生成 `doing/tasks.json`。

```bash
sense doing dag job_1
```

**前提：** plan 目录下存在 task*.md 文件。
**产出：** `.sense/jobs/job_1/doing/tasks.json`

### `sense doing next_task <job_id>`
返回下一个可执行的 task ID（所有依赖已 success 的第一个 pending task）。

```bash
sense doing next_task job_1
# 输出: task1（或 NONE）
```

### `sense doing update_task <job_id> <task_id> <status>`
更新 tasks.json 中指定 task 的状态。

```bash
sense doing update_task job_1 task1 success --commit abc1234
sense doing update_task job_1 task1 failed --attempts 2
```

**状态值：** `pending` | `running` | `success` | `failed`

**注意：** `status` 是位置参数，不是 `--status` flag。

### `sense doing list <job_id>`
以表格形式展示所有任务状态。

```bash
sense doing list job_1
```

---

## Learning 阶段

### `sense learning merge <job_id>`
将 learning 产物合并到 `.sense/` 项目上下文。

```bash
sense learning merge job_1
```

**合并规则：**
- `learning/wiki/` → `.sense/wiki/`（覆盖同名文件）
- `learning/skills/` → `.sense/skills/`
- `learning/OKR.md` / `learning/SPEC.md` → `.sense/OKR.md` / `.sense/SPEC.md`（直接覆盖）

---

## Tools 工具命令

### `sense tools gen_prompt <phase> <job_id> [task_id]`
生成指定阶段的 prompt 文件，输出到 `.sense/jobs/{job_id}/prompts/`。

```bash
sense tools gen_prompt plan job_1
# → .sense/jobs/job_1/prompts/plan_job_1.md

sense tools gen_prompt doing job_1 task1
# → .sense/jobs/job_1/prompts/doing_job_1_task1.md

sense tools gen_prompt learning job_1
# → .sense/jobs/job_1/prompts/learning_job_1.md
```

**自动注入内容：**
- 所有 phase：OKR、SPEC、wiki、skills
- task 相关 phase（doing/test/review）：task_name、task_goal、task_key_results、task_test_methods、test_script_path
- learning phase：job_summary（tasks.json + debug.md 内容）

### `sense tools plan_check <job_id> [--json]`
验证 plan 目录质量。

**检查项：**
- plan/ 下存在至少一个 task*.md
- 每个 task.md 包含五个必要 section
- 依赖关系无循环（支持逗号分隔格式）

```bash
sense tools plan_check job_1
sense tools plan_check job_1 --json
# {"pass": true, "errors": []}
```

### `sense tools doing_check <job_id> [--json]`
验证 doing 目录质量。

**检查项：**
- tasks.json 存在且格式合法
- 无 zombie task（status=running 视为 zombie）

### `sense tools learning_check <job_id> [--json]`
验证 learning 产物质量。

**检查项：**
- `.sense/jobs/{job_id}/README.md` 存在（在 job 根目录，不是 learning/ 子目录）
- `learning/skills/*.py` 语法合法（`python3 -m py_compile`）
