#!/usr/bin/env python3
"""task2 test: update_task 命令签名与 SKILL.md 一致"""
import json, os, subprocess, sys, tempfile

SENSE_BIN = os.environ.get("SENSE_BIN", os.path.expanduser("~/.local/bin/sense"))
errors = []

def run(cmd, cwd=None):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

def make_workspace_with_tasks(tmp):
    run(f"{SENSE_BIN} init", cwd=tmp)
    import textwrap
    plan_dir = os.path.join(tmp, ".sense", "jobs", "job_1", "plan")
    os.makedirs(plan_dir, exist_ok=True)
    task1 = textwrap.dedent("""\
        # 依赖关系
        （无）

        # 任务名称
        测试任务

        # 任务目标
        测试目标

        # 关键结果
        1. 结果

        # 测试方法
        1. 测试
    """)
    with open(os.path.join(plan_dir, "task1.md"), "w") as f:
        f.write(task1)
    run(f"{SENSE_BIN} doing dag job_1", cwd=tmp)

# ── Case 1: 位置参数形式（无 --commit）能正确执行 ─────────────────────────
with tempfile.TemporaryDirectory() as tmp:
    make_workspace_with_tasks(tmp)
    rc, out, err = run(f"{SENSE_BIN} doing update_task job_1 task1 success", cwd=tmp)
    if rc != 0:
        errors.append(f"Case1: update_task positional failed: {err}")
    else:
        tasks_path = os.path.join(tmp, ".sense", "jobs", "job_1", "doing", "tasks.json")
        with open(tasks_path) as f:
            tj = json.load(f)
        task1 = tj["tasks"][0]
        if task1["status"] != "success":
            errors.append(f"Case1: expected status=success, got {task1['status']}")

# ── Case 2: 位置参数 + --commit 能正确执行 ───────────────────────────────
with tempfile.TemporaryDirectory() as tmp:
    make_workspace_with_tasks(tmp)
    rc, out, err = run(f"{SENSE_BIN} doing update_task job_1 task1 success --commit abc1234", cwd=tmp)
    if rc != 0:
        errors.append(f"Case2: update_task with --commit failed: {err}")
    else:
        tasks_path = os.path.join(tmp, ".sense", "jobs", "job_1", "doing", "tasks.json")
        with open(tasks_path) as f:
            tj = json.load(f)
        task1 = tj["tasks"][0]
        if task1["commit_hash"] != "abc1234":
            errors.append(f"Case2: expected commit_hash=abc1234, got {task1['commit_hash']!r}")

# ── Case 3: --status flag 形式应该失败（确认旧写法不再工作） ──────────────
with tempfile.TemporaryDirectory() as tmp:
    make_workspace_with_tasks(tmp)
    rc, out, err = run(f"{SENSE_BIN} doing update_task job_1 task1 --status success", cwd=tmp)
    if rc == 0:
        errors.append("Case3: --status flag form should fail but succeeded")

# ── Case 4: SKILL.md 中不含 --status 写法 ────────────────────────────────
skill_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "..", "..", "..", "..",
    "opt", "meituan", "dolphinfs_sunquan20", "ai_coding", "Coding", "sense",
    "skills", "sense-ai-loop", "SKILL.md"
)
# 用绝对路径
skill_path = "/opt/meituan/dolphinfs_sunquan20/ai_coding/Coding/sense/skills/sense-ai-loop/SKILL.md"
with open(skill_path) as f:
    skill_content = f.read()
if "--status" in skill_content:
    errors.append("Case4: SKILL.md still contains '--status' flag form")

result = {"pass": len(errors) == 0, "errors": errors}
print(json.dumps(result, ensure_ascii=False))
sys.exit(0 if result["pass"] else 1)
