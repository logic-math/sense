#!/usr/bin/env python3
"""task1 test: parser 支持逗号分隔依赖"""
import json, os, subprocess, sys, tempfile, textwrap

SENSE_BIN = os.environ.get("SENSE_BIN", os.path.expanduser("~/.local/bin/sense"))
errors = []

def run(cmd, cwd=None):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

# ── 辅助：在 tmpdir 建立最小 sense workspace ──────────────────────────────
def make_workspace(tmp):
    rc, _, e = run(f"{SENSE_BIN} init", cwd=tmp)
    if rc != 0:
        errors.append(f"sense init failed: {e}")
        return False
    return True

def write_task(plan_dir, fname, deps, name="任务名", goal="目标", kr="结果", test="测试"):
    content = textwrap.dedent(f"""\
        # 依赖关系
        {deps}

        # 任务名称
        {name}

        # 任务目标
        {goal}

        # 关键结果
        1. {kr}

        # 测试方法
        1. {test}
    """)
    os.makedirs(plan_dir, exist_ok=True)
    with open(os.path.join(plan_dir, fname), "w") as f:
        f.write(content)

# ── Case 1: 逗号分隔依赖被正确解析 ───────────────────────────────────────
with tempfile.TemporaryDirectory() as tmp:
    if make_workspace(tmp):
        plan_dir = os.path.join(tmp, ".sense", "jobs", "job_1", "plan")
        write_task(plan_dir, "task1.md", "（无）", name="任务一")
        write_task(plan_dir, "task2.md", "（无）", name="任务二")
        write_task(plan_dir, "task3.md", "task1, task2", name="任务三")  # 逗号分隔

        rc, out, err = run(f"{SENSE_BIN} doing dag job_1", cwd=tmp)
        if rc != 0:
            errors.append(f"Case1: dag failed with comma deps: {err}")
        else:
            tasks_path = os.path.join(tmp, ".sense", "jobs", "job_1", "doing", "tasks.json")
            with open(tasks_path) as f:
                tj = json.load(f)
            task3 = next((t for t in tj["tasks"] if t["task_id"] == "task3"), None)
            if task3 is None:
                errors.append("Case1: task3 not found in tasks.json")
            elif task3["dependencies"] != ["task1", "task2"]:
                errors.append(f"Case1: expected deps ['task1','task2'], got {task3['dependencies']}")

# ── Case 2: 换行分隔依赖（原有格式）仍然正确 ─────────────────────────────
with tempfile.TemporaryDirectory() as tmp:
    if make_workspace(tmp):
        plan_dir = os.path.join(tmp, ".sense", "jobs", "job_1", "plan")
        write_task(plan_dir, "task1.md", "（无）")
        write_task(plan_dir, "task2.md", "task1")  # 换行（单行）

        rc, out, err = run(f"{SENSE_BIN} doing dag job_1", cwd=tmp)
        if rc != 0:
            errors.append(f"Case2: dag failed with newline deps: {err}")
        else:
            tasks_path = os.path.join(tmp, ".sense", "jobs", "job_1", "doing", "tasks.json")
            with open(tasks_path) as f:
                tj = json.load(f)
            task2 = next((t for t in tj["tasks"] if t["task_id"] == "task2"), None)
            if task2 is None:
                errors.append("Case2: task2 not found")
            elif task2["dependencies"] != ["task1"]:
                errors.append(f"Case2: expected ['task1'], got {task2['dependencies']}")

# ── Case 3: （无）解析为空依赖 ────────────────────────────────────────────
with tempfile.TemporaryDirectory() as tmp:
    if make_workspace(tmp):
        plan_dir = os.path.join(tmp, ".sense", "jobs", "job_1", "plan")
        write_task(plan_dir, "task1.md", "（无）")

        rc, out, err = run(f"{SENSE_BIN} doing dag job_1", cwd=tmp)
        if rc != 0:
            errors.append(f"Case3: dag failed: {err}")
        else:
            tasks_path = os.path.join(tmp, ".sense", "jobs", "job_1", "doing", "tasks.json")
            with open(tasks_path) as f:
                tj = json.load(f)
            task1 = tj["tasks"][0]
            deps = task1.get("dependencies") or []
            if deps:
                errors.append(f"Case3: expected empty deps, got {deps}")

# ── Case 4: job_1 的 task4.md（task2, task3）能被正确处理 ─────────────────
job1_plan = "/home/sankuai/dolphinfs_sunquan20/ai_coding/.sense/jobs/job_1/plan"
if os.path.isdir(job1_plan):
    with tempfile.TemporaryDirectory() as tmp:
        if make_workspace(tmp):
            import shutil
            dst_plan = os.path.join(tmp, ".sense", "jobs", "job_1", "plan")
            shutil.copytree(job1_plan, dst_plan)
            rc, out, err = run(f"{SENSE_BIN} doing dag job_1", cwd=tmp)
            if rc != 0:
                errors.append(f"Case4: job_1 dag failed: {err}")

# ── Case 5: plan_check 对逗号分隔依赖也能通过 ─────────────────────────────
with tempfile.TemporaryDirectory() as tmp:
    if make_workspace(tmp):
        plan_dir = os.path.join(tmp, ".sense", "jobs", "job_1", "plan")
        write_task(plan_dir, "task1.md", "（无）")
        write_task(plan_dir, "task2.md", "（无）")
        write_task(plan_dir, "task3.md", "task1, task2")

        rc, out, err = run(f"{SENSE_BIN} tools plan_check job_1 --json", cwd=tmp)
        try:
            result = json.loads(out)
            if not result.get("pass"):
                errors.append(f"Case5: plan_check failed: {result.get('errors')}")
        except Exception as e:
            errors.append(f"Case5: plan_check output not JSON: {out!r} {err!r}")

result = {"pass": len(errors) == 0, "errors": errors}
print(json.dumps(result, ensure_ascii=False))
sys.exit(0 if result["pass"] else 1)
