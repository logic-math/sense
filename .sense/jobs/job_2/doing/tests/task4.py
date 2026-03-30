#!/usr/bin/env python3
"""task4 test: gen_prompt 输出路径 + learning_check 路径修复"""
import json, os, subprocess, sys, tempfile, textwrap

SENSE_BIN = os.environ.get("SENSE_BIN", os.path.expanduser("~/.local/bin/sense"))
errors = []

def run(cmd, cwd=None):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

def make_workspace_with_plan(tmp):
    run(f"{SENSE_BIN} init", cwd=tmp)
    plan_dir = os.path.join(tmp, ".sense", "jobs", "job_1", "plan")
    os.makedirs(plan_dir, exist_ok=True)
    task1 = textwrap.dedent("""\
        # 依赖关系
        （无）

        # 任务名称
        测试任务

        # 任务目标
        目标

        # 关键结果
        1. 结果

        # 测试方法
        1. 测试
    """)
    with open(os.path.join(plan_dir, "task1.md"), "w") as f:
        f.write(task1)
    # 需要 tasks.json for learning
    doing_dir = os.path.join(tmp, ".sense", "jobs", "job_1", "doing")
    os.makedirs(doing_dir, exist_ok=True)
    tasks_json = {"version": "1.0", "created_at": "2026-03-30T00:00:00+08:00",
                  "updated_at": "2026-03-30T00:00:00+08:00",
                  "tasks": [{"task_id": "task1", "task_name": "测试任务", "task_file": "task1.md",
                              "status": "success", "dependencies": None, "attempts": 0,
                              "commit_hash": "", "created_at": "2026-03-30T00:00:00+08:00",
                              "updated_at": "2026-03-30T00:00:00+08:00"}]}
    with open(os.path.join(doing_dir, "tasks.json"), "w") as f:
        json.dump(tasks_json, f)

# ── Case 1: gen_prompt plan 输出到 .sense/jobs/job_1/prompts/ ─────────────
with tempfile.TemporaryDirectory() as tmp:
    make_workspace_with_plan(tmp)
    rc, out, err = run(f"{SENSE_BIN} tools gen_prompt plan job_1", cwd=tmp)
    if rc != 0:
        errors.append(f"Case1: gen_prompt plan failed: {err}")
    else:
        expected = os.path.join(tmp, ".sense", "jobs", "job_1", "prompts", "plan_job_1.md")
        if not os.path.exists(expected):
            errors.append(f"Case1: prompt not at expected path {expected}")
        # 确认旧路径 <cwd>/prompts/ 不存在
        old_path = os.path.join(tmp, "prompts", "plan_job_1.md")
        if os.path.exists(old_path):
            errors.append(f"Case1: prompt also written to old path {old_path}")

# ── Case 2: gen_prompt doing 输出到 .sense/jobs/job_1/prompts/ ───────────
with tempfile.TemporaryDirectory() as tmp:
    make_workspace_with_plan(tmp)
    rc, out, err = run(f"{SENSE_BIN} tools gen_prompt doing job_1 task1", cwd=tmp)
    if rc != 0:
        errors.append(f"Case2: gen_prompt doing failed: {err}")
    else:
        expected = os.path.join(tmp, ".sense", "jobs", "job_1", "prompts", "doing_job_1_task1.md")
        if not os.path.exists(expected):
            errors.append(f"Case2: prompt not at expected path {expected}")

# ── Case 3: learning_check 在 job 根目录有 README.md 时 PASS ─────────────
with tempfile.TemporaryDirectory() as tmp:
    make_workspace_with_plan(tmp)
    # 在 job 根目录创建 README.md
    job_dir = os.path.join(tmp, ".sense", "jobs", "job_1")
    with open(os.path.join(job_dir, "README.md"), "w") as f:
        f.write("# Job 1 Summary\n")
    rc, out, err = run(f"{SENSE_BIN} tools learning_check job_1 --json", cwd=tmp)
    try:
        result = json.loads(out)
        if not result.get("pass"):
            errors.append(f"Case3: learning_check should PASS but got: {result.get('errors')}")
    except Exception:
        errors.append(f"Case3: output not JSON: {out!r} {err!r}")

# ── Case 4: learning_check 在没有 README.md 时 FAIL，错误信息含正确路径 ──
with tempfile.TemporaryDirectory() as tmp:
    make_workspace_with_plan(tmp)
    rc, out, err = run(f"{SENSE_BIN} tools learning_check job_1 --json", cwd=tmp)
    try:
        result = json.loads(out)
        if result.get("pass"):
            errors.append("Case4: learning_check should FAIL without README.md")
        else:
            # 错误信息应包含 job 根目录路径（不是 learning/ 子目录）
            errs = " ".join(result.get("errors", []))
            if "learning/README.md" in errs and "jobs/job_1/README.md" not in errs:
                errors.append(f"Case4: error message still references old path: {errs}")
    except Exception:
        errors.append(f"Case4: output not JSON: {out!r} {err!r}")

# ── Case 5: learning_check 在 learning/README.md（旧路径）时应 FAIL ───────
with tempfile.TemporaryDirectory() as tmp:
    make_workspace_with_plan(tmp)
    # 在旧路径创建 README.md（learning/ 子目录）
    learning_dir = os.path.join(tmp, ".sense", "jobs", "job_1", "learning")
    os.makedirs(learning_dir, exist_ok=True)
    with open(os.path.join(learning_dir, "README.md"), "w") as f:
        f.write("# wrong location\n")
    rc, out, err = run(f"{SENSE_BIN} tools learning_check job_1 --json", cwd=tmp)
    try:
        result = json.loads(out)
        if result.get("pass"):
            errors.append("Case5: learning_check should FAIL when README.md is in learning/ not job root")
    except Exception:
        errors.append(f"Case5: output not JSON: {out!r} {err!r}")

result = {"pass": len(errors) == 0, "errors": errors}
print(json.dumps(result, ensure_ascii=False))
sys.exit(0 if result["pass"] else 1)
