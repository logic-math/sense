#!/usr/bin/env python3
import json
import sys
import os
import subprocess
import tempfile
import shutil

PROJECT_ROOT = "/Users/sunquan/ai_coding/CODING/sense"
BINARY = os.path.join(PROJECT_ROOT, "bin", "sense")


def run_cmd(args, cwd=None, env=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=env)


def make_task_md(path, task_id, deps=None):
    """Write a minimal task .md file."""
    dep_line = "（无）" if not deps else "\n".join(deps)
    content = f"# 依赖关系\n{dep_line}\n\n# 任务名称\n{task_id}\n\n# 任务目标\ntest\n\n# 关键结果\n1. test\n\n# 测试方法\n1. test\n"
    with open(path, "w") as f:
        f.write(content)


def main():
    errors = []

    # Ensure binary exists
    if not os.path.exists(BINARY):
        # Try to build first
        r = run_cmd(["go", "build", "-o", "bin/sense", "./cmd/sense/..."], cwd=PROJECT_ROOT)
        if r.returncode != 0:
            errors.append(f"binary not found and build failed: {r.stderr.strip()}")
            print(json.dumps({"pass": False, "errors": errors}))
            sys.exit(1)

    # -----------------------------------------------------------------------
    # Test 1: sense doing dag generates correct tasks.json from plan/*.md
    # -----------------------------------------------------------------------
    tmpdir1 = tempfile.mkdtemp()
    try:
        sense_dir = os.path.join(tmpdir1, ".sense")
        job_dir = os.path.join(sense_dir, "jobs", "job_1")
        plan_dir = os.path.join(job_dir, "plan")
        doing_dir = os.path.join(job_dir, "doing")
        os.makedirs(plan_dir, exist_ok=True)
        os.makedirs(doing_dir, exist_ok=True)

        make_task_md(os.path.join(plan_dir, "task1.md"), "task1", deps=None)
        make_task_md(os.path.join(plan_dir, "task2.md"), "task2", deps=["task1"])

        r = run_cmd([BINARY, "doing", "dag", "job_1"], cwd=tmpdir1)
        if r.returncode != 0:
            errors.append(f"Test1: sense doing dag failed (exit {r.returncode}): {r.stderr.strip()}")
        else:
            tasks_json_path = os.path.join(doing_dir, "tasks.json")
            if not os.path.exists(tasks_json_path):
                errors.append(f"Test1: tasks.json not created at {tasks_json_path}")
            else:
                try:
                    with open(tasks_json_path) as f:
                        tj = json.load(f)
                    if "version" not in tj:
                        errors.append("Test1: tasks.json missing 'version' field")
                    if "tasks" not in tj or not isinstance(tj["tasks"], list):
                        errors.append("Test1: tasks.json missing or invalid 'tasks' array")
                    else:
                        if len(tj["tasks"]) != 2:
                            errors.append(f"Test1: expected 2 tasks, got {len(tj['tasks'])}")
                        for t in tj["tasks"]:
                            if t.get("status") != "pending":
                                errors.append(f"Test1: task {t.get('task_id')} status={t.get('status')}, expected pending")
                except Exception as e:
                    errors.append(f"Test1: failed to parse tasks.json: {str(e)}")
    except Exception as e:
        errors.append(f"Test1 exception: {str(e)}")
    finally:
        shutil.rmtree(tmpdir1, ignore_errors=True)

    # -----------------------------------------------------------------------
    # Test 2: cyclic dependency causes non-zero exit and error output
    # -----------------------------------------------------------------------
    tmpdir2 = tempfile.mkdtemp()
    try:
        sense_dir = os.path.join(tmpdir2, ".sense")
        job_dir = os.path.join(sense_dir, "jobs", "job_1")
        plan_dir = os.path.join(job_dir, "plan")
        doing_dir = os.path.join(job_dir, "doing")
        os.makedirs(plan_dir, exist_ok=True)
        os.makedirs(doing_dir, exist_ok=True)

        # task1 depends on task2, task2 depends on task1 → cycle
        make_task_md(os.path.join(plan_dir, "task1.md"), "task1", deps=["task2"])
        make_task_md(os.path.join(plan_dir, "task2.md"), "task2", deps=["task1"])

        r = run_cmd([BINARY, "doing", "dag", "job_1"], cwd=tmpdir2)
        if r.returncode == 0:
            errors.append("Test2: expected non-zero exit for cyclic dependency, got 0")
        combined = r.stdout + r.stderr
        if not combined.strip():
            errors.append("Test2: expected error output for cyclic dependency, got none")
    except Exception as e:
        errors.append(f"Test2 exception: {str(e)}")
    finally:
        shutil.rmtree(tmpdir2, ignore_errors=True)

    # -----------------------------------------------------------------------
    # Test 3: next_task returns task1 when task1=pending, task2=pending(dep task1)
    # -----------------------------------------------------------------------
    tmpdir3 = tempfile.mkdtemp()
    try:
        sense_dir = os.path.join(tmpdir3, ".sense")
        job_dir = os.path.join(sense_dir, "jobs", "job_1")
        doing_dir = os.path.join(job_dir, "doing")
        os.makedirs(doing_dir, exist_ok=True)

        tasks_json = {
            "version": "1.0",
            "tasks": [
                {"task_id": "task1", "task_name": "task1", "status": "pending", "dependencies": None},
                {"task_id": "task2", "task_name": "task2", "status": "pending", "dependencies": ["task1"]},
            ]
        }
        with open(os.path.join(doing_dir, "tasks.json"), "w") as f:
            json.dump(tasks_json, f)

        r = run_cmd([BINARY, "doing", "next_task", "job_1"], cwd=tmpdir3)
        if r.returncode != 0:
            errors.append(f"Test3: next_task failed (exit {r.returncode}): {r.stderr.strip()}")
        else:
            output = r.stdout.strip()
            if output != "task1":
                errors.append(f"Test3: expected 'task1', got '{output}'")
    except Exception as e:
        errors.append(f"Test3 exception: {str(e)}")
    finally:
        shutil.rmtree(tmpdir3, ignore_errors=True)

    # -----------------------------------------------------------------------
    # Test 4: next_task returns task2 when task1=success, task2=pending
    # -----------------------------------------------------------------------
    tmpdir4 = tempfile.mkdtemp()
    try:
        sense_dir = os.path.join(tmpdir4, ".sense")
        job_dir = os.path.join(sense_dir, "jobs", "job_1")
        doing_dir = os.path.join(job_dir, "doing")
        os.makedirs(doing_dir, exist_ok=True)

        tasks_json = {
            "version": "1.0",
            "tasks": [
                {"task_id": "task1", "task_name": "task1", "status": "success", "dependencies": None},
                {"task_id": "task2", "task_name": "task2", "status": "pending", "dependencies": ["task1"]},
            ]
        }
        with open(os.path.join(doing_dir, "tasks.json"), "w") as f:
            json.dump(tasks_json, f)

        r = run_cmd([BINARY, "doing", "next_task", "job_1"], cwd=tmpdir4)
        if r.returncode != 0:
            errors.append(f"Test4: next_task failed (exit {r.returncode}): {r.stderr.strip()}")
        else:
            output = r.stdout.strip()
            if output != "task2":
                errors.append(f"Test4: expected 'task2', got '{output}'")
    except Exception as e:
        errors.append(f"Test4 exception: {str(e)}")
    finally:
        shutil.rmtree(tmpdir4, ignore_errors=True)

    # -----------------------------------------------------------------------
    # Test 5: next_task returns NONE when all tasks=success
    # -----------------------------------------------------------------------
    tmpdir5 = tempfile.mkdtemp()
    try:
        sense_dir = os.path.join(tmpdir5, ".sense")
        job_dir = os.path.join(sense_dir, "jobs", "job_1")
        doing_dir = os.path.join(job_dir, "doing")
        os.makedirs(doing_dir, exist_ok=True)

        tasks_json = {
            "version": "1.0",
            "tasks": [
                {"task_id": "task1", "task_name": "task1", "status": "success", "dependencies": None},
                {"task_id": "task2", "task_name": "task2", "status": "success", "dependencies": ["task1"]},
            ]
        }
        with open(os.path.join(doing_dir, "tasks.json"), "w") as f:
            json.dump(tasks_json, f)

        r = run_cmd([BINARY, "doing", "next_task", "job_1"], cwd=tmpdir5)
        if r.returncode != 0:
            errors.append(f"Test5: next_task failed (exit {r.returncode}): {r.stderr.strip()}")
        else:
            output = r.stdout.strip()
            if output != "NONE":
                errors.append(f"Test5: expected 'NONE', got '{output}'")
    except Exception as e:
        errors.append(f"Test5 exception: {str(e)}")
    finally:
        shutil.rmtree(tmpdir5, ignore_errors=True)

    result = {
        "pass": len(errors) == 0,
        "errors": errors,
    }

    print(json.dumps(result))
    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
