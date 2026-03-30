#!/usr/bin/env python3
"""task3 test: learning prompt 中 {{job_summary}} 被正确注入"""
import json, os, subprocess, sys, tempfile, textwrap

SENSE_BIN = os.environ.get("SENSE_BIN", os.path.expanduser("~/.local/bin/sense"))
errors = []

def run(cmd, cwd=None):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

def make_full_workspace(tmp):
    """创建带 plan + tasks.json + debug.md 的 workspace"""
    run(f"{SENSE_BIN} init", cwd=tmp)
    plan_dir = os.path.join(tmp, ".sense", "jobs", "job_1", "plan")
    os.makedirs(plan_dir, exist_ok=True)
    task1 = textwrap.dedent("""\
        # 依赖关系
        （无）

        # 任务名称
        实现核心功能

        # 任务目标
        实现主要逻辑

        # 关键结果
        1. 功能完成

        # 测试方法
        1. 运行测试脚本
    """)
    with open(os.path.join(plan_dir, "task1.md"), "w") as f:
        f.write(task1)

    # 手动创建 tasks.json（已 success）
    doing_dir = os.path.join(tmp, ".sense", "jobs", "job_1", "doing")
    os.makedirs(doing_dir, exist_ok=True)
    tasks_json = {
        "version": "1.0",
        "created_at": "2026-03-30T00:00:00+08:00",
        "updated_at": "2026-03-30T00:00:00+08:00",
        "tasks": [{
            "task_id": "task1",
            "task_name": "实现核心功能",
            "task_file": "task1.md",
            "status": "success",
            "dependencies": None,
            "attempts": 0,
            "commit_hash": "abc1234",
            "created_at": "2026-03-30T00:00:00+08:00",
            "updated_at": "2026-03-30T00:00:00+08:00"
        }]
    }
    with open(os.path.join(doing_dir, "tasks.json"), "w") as f:
        json.dump(tasks_json, f)

    # 创建 debug.md
    with open(os.path.join(doing_dir, "debug.md"), "w") as f:
        f.write("## task1: 实现核心功能\n\n**分析过程**: 分析了现有代码\n\n**验证结果**: ✅ 通过\n")

# ── Case 1: 生成的 learning prompt 不含 {{job_summary}} 字面量 ────────────
with tempfile.TemporaryDirectory() as tmp:
    make_full_workspace(tmp)
    rc, out, err = run(f"{SENSE_BIN} tools gen_prompt learning job_1", cwd=tmp)
    if rc != 0:
        errors.append(f"Case1: gen_prompt learning failed: {err}")
    else:
        # 找到生成的 prompt 文件
        prompts_dir = os.path.join(tmp, ".sense", "jobs", "job_1", "prompts")
        prompt_file = os.path.join(prompts_dir, "learning_job_1.md")
        if not os.path.exists(prompt_file):
            errors.append(f"Case1: prompt file not found at {prompt_file}")
        else:
            with open(prompt_file) as f:
                content = f.read()
            if "{{job_summary}}" in content:
                errors.append("Case1: prompt still contains {{job_summary}} literal")
            if "task1" not in content and "实现核心功能" not in content:
                errors.append("Case1: prompt does not contain task info from tasks.json")

# ── Case 2: tasks.json 内容出现在 prompt 中 ───────────────────────────────
with tempfile.TemporaryDirectory() as tmp:
    make_full_workspace(tmp)
    run(f"{SENSE_BIN} tools gen_prompt learning job_1", cwd=tmp)
    prompt_file = os.path.join(tmp, ".sense", "jobs", "job_1", "prompts", "learning_job_1.md")
    if os.path.exists(prompt_file):
        with open(prompt_file) as f:
            content = f.read()
        if "abc1234" not in content:
            errors.append("Case2: commit hash from tasks.json not found in prompt")

# ── Case 3: debug.md 内容也出现在 prompt 中 ──────────────────────────────
with tempfile.TemporaryDirectory() as tmp:
    make_full_workspace(tmp)
    run(f"{SENSE_BIN} tools gen_prompt learning job_1", cwd=tmp)
    prompt_file = os.path.join(tmp, ".sense", "jobs", "job_1", "prompts", "learning_job_1.md")
    if os.path.exists(prompt_file):
        with open(prompt_file) as f:
            content = f.read()
        if "分析过程" not in content:
            errors.append("Case3: debug.md content not found in prompt")

# ── Case 4: debug.md 不存在时命令仍然成功 ────────────────────────────────
with tempfile.TemporaryDirectory() as tmp:
    make_full_workspace(tmp)
    # 删除 debug.md
    debug_path = os.path.join(tmp, ".sense", "jobs", "job_1", "doing", "debug.md")
    if os.path.exists(debug_path):
        os.remove(debug_path)
    rc, out, err = run(f"{SENSE_BIN} tools gen_prompt learning job_1", cwd=tmp)
    if rc != 0:
        errors.append(f"Case4: gen_prompt without debug.md failed: {err}")

result = {"pass": len(errors) == 0, "errors": errors}
print(json.dumps(result, ensure_ascii=False))
sys.exit(0 if result["pass"] else 1)
