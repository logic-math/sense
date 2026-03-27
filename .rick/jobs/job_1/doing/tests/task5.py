#!/usr/bin/env python3
import json
import sys
import os
import subprocess
import tempfile
import shutil

PROJECT_ROOT = "/Users/sunquan/ai_coding/CODING/sense"
BINARY = os.path.join(PROJECT_ROOT, "bin", "sense")


def build_binary(errors):
    """Build the binary, return True if successful."""
    try:
        result = subprocess.run(
            ["go", "build", "-o", "bin/sense", "./cmd/sense/..."],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            errors.append(f"go build failed: {result.stderr.strip()}")
            return False
        return True
    except Exception as e:
        errors.append(f"go build exception: {str(e)}")
        return False


def make_tasks_json(tasks_list):
    return {
        "version": "1.0",
        "tasks": tasks_list,
    }


def main():
    errors = []

    # Build binary first
    if not build_binary(errors):
        result = {"pass": False, "errors": errors}
        print(json.dumps(result))
        sys.exit(1)

    tmpdir = tempfile.mkdtemp()
    try:
        # Setup .sense directory structure
        sense_dir = os.path.join(tmpdir, ".sense")
        jobs_dir = os.path.join(sense_dir, "jobs")
        job_dir = os.path.join(jobs_dir, "job_1")
        doing_dir = os.path.join(job_dir, "doing")
        learning_dir = os.path.join(job_dir, "learning")

        os.makedirs(doing_dir, exist_ok=True)
        os.makedirs(learning_dir, exist_ok=True)

        tasks_json_path = os.path.join(doing_dir, "tasks.json")

        # Test 1: 创建 tasks.json（task1=pending），运行 update_task，验证 status=success 且 commit_hash=abc1234
        try:
            initial_tasks = make_tasks_json([
                {
                    "task_id": "task1",
                    "task_name": "测试任务",
                    "status": "pending",
                    "dependencies": None,
                    "attempts": 0,
                }
            ])
            with open(tasks_json_path, "w") as f:
                json.dump(initial_tasks, f)

            result = subprocess.run(
                [BINARY, "doing", "update_task", "job_1", "task1", "success", "--commit", "abc1234"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                errors.append(
                    f"Test1: update_task expected exit 0, got {result.returncode}. "
                    f"stdout={result.stdout.strip()} stderr={result.stderr.strip()}"
                )
            else:
                try:
                    with open(tasks_json_path, "r") as f:
                        updated = json.load(f)
                    task1 = next((t for t in updated.get("tasks", []) if t["task_id"] == "task1"), None)
                    if task1 is None:
                        errors.append("Test1: task1 not found in tasks.json after update_task")
                    else:
                        if task1.get("status") != "success":
                            errors.append(
                                f"Test1: expected task1.status=success, got {task1.get('status')!r}"
                            )
                        if task1.get("commit_hash") != "abc1234":
                            errors.append(
                                f"Test1: expected task1.commit_hash=abc1234, got {task1.get('commit_hash')!r}"
                            )
                except Exception as e:
                    errors.append(f"Test1: failed to read/parse tasks.json after update: {str(e)}")
        except Exception as e:
            errors.append(f"Test1 exception: {str(e)}")

        # Test 2: 运行两次相同的 update_task 命令，验证结果幂等（第二次不报错，状态保持一致）
        try:
            # Re-create tasks.json with task1=pending
            with open(tasks_json_path, "w") as f:
                json.dump(make_tasks_json([
                    {
                        "task_id": "task1",
                        "task_name": "测试任务",
                        "status": "pending",
                        "dependencies": None,
                        "attempts": 0,
                    }
                ]), f)

            cmd = [BINARY, "doing", "update_task", "job_1", "task1", "success", "--commit", "abc1234"]

            result1 = subprocess.run(cmd, cwd=tmpdir, capture_output=True, text=True)
            if result1.returncode != 0:
                errors.append(
                    f"Test2: first update_task failed with exit {result1.returncode}. "
                    f"stderr={result1.stderr.strip()}"
                )
            else:
                result2 = subprocess.run(cmd, cwd=tmpdir, capture_output=True, text=True)
                if result2.returncode != 0:
                    errors.append(
                        f"Test2: second (idempotent) update_task failed with exit {result2.returncode}. "
                        f"stderr={result2.stderr.strip()}"
                    )
                else:
                    try:
                        with open(tasks_json_path, "r") as f:
                            updated = json.load(f)
                        task1 = next((t for t in updated.get("tasks", []) if t["task_id"] == "task1"), None)
                        if task1 is None or task1.get("status") != "success":
                            errors.append(
                                f"Test2: after idempotent update, task1.status expected success, "
                                f"got {task1.get('status') if task1 else 'None'!r}"
                            )
                    except Exception as e:
                        errors.append(f"Test2: failed to read tasks.json after idempotent update: {str(e)}")
        except Exception as e:
            errors.append(f"Test2 exception: {str(e)}")

        # Test 3: 创建 learning/wiki/arch.md 和 learning/skills/check.py，
        #         运行 sense learning merge job_1，验证文件被复制到 .sense/wiki/ 和 .sense/skills/
        try:
            wiki_dir = os.path.join(learning_dir, "wiki")
            skills_dir = os.path.join(learning_dir, "skills")
            os.makedirs(wiki_dir, exist_ok=True)
            os.makedirs(skills_dir, exist_ok=True)

            arch_md_path = os.path.join(wiki_dir, "arch.md")
            check_py_path = os.path.join(skills_dir, "check.py")

            with open(arch_md_path, "w") as f:
                f.write("# Architecture\n\nThis is the arch doc.\n")
            with open(check_py_path, "w") as f:
                f.write("#!/usr/bin/env python3\n# check skill\nprint('ok')\n")

            result = subprocess.run(
                [BINARY, "learning", "merge", "job_1"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                errors.append(
                    f"Test3: learning merge expected exit 0, got {result.returncode}. "
                    f"stdout={result.stdout.strip()} stderr={result.stderr.strip()}"
                )
            else:
                dest_wiki = os.path.join(sense_dir, "wiki", "arch.md")
                dest_skills = os.path.join(sense_dir, "skills", "check.py")

                if not os.path.exists(dest_wiki):
                    errors.append(
                        f"Test3: expected .sense/wiki/arch.md to exist after learning merge, but it does not. "
                        f"(looked at {dest_wiki})"
                    )
                if not os.path.exists(dest_skills):
                    errors.append(
                        f"Test3: expected .sense/skills/check.py to exist after learning merge, but it does not. "
                        f"(looked at {dest_skills})"
                    )
        except Exception as e:
            errors.append(f"Test3 exception: {str(e)}")

        # Test 4: 运行 sense doing list job_1，验证输出包含 task ID 和状态列
        try:
            # Ensure tasks.json has at least one task
            with open(tasks_json_path, "w") as f:
                json.dump(make_tasks_json([
                    {
                        "task_id": "task1",
                        "task_name": "测试任务",
                        "status": "success",
                        "dependencies": None,
                        "attempts": 1,
                    }
                ]), f)

            result = subprocess.run(
                [BINARY, "doing", "list", "job_1"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                errors.append(
                    f"Test4: doing list expected exit 0, got {result.returncode}. "
                    f"stderr={result.stderr.strip()}"
                )
            else:
                combined = result.stdout + result.stderr
                if "task1" not in combined:
                    errors.append(
                        f"Test4: doing list output does not contain task ID 'task1'. "
                        f"stdout={result.stdout.strip()!r}"
                    )
                # Check for status column (any of the known status values or a header)
                status_present = any(
                    s in combined for s in ["success", "pending", "running", "failed", "status", "STATUS"]
                )
                if not status_present:
                    errors.append(
                        f"Test4: doing list output does not contain a status column. "
                        f"stdout={result.stdout.strip()!r}"
                    )
        except Exception as e:
            errors.append(f"Test4 exception: {str(e)}")

        # Test 5: 验证 sense doing update_task 对不存在的 task_id 返回非零退出码和错误信息
        try:
            # Ensure tasks.json exists but does NOT contain 'nonexistent_task'
            with open(tasks_json_path, "w") as f:
                json.dump(make_tasks_json([
                    {
                        "task_id": "task1",
                        "task_name": "测试任务",
                        "status": "pending",
                        "dependencies": None,
                        "attempts": 0,
                    }
                ]), f)

            result = subprocess.run(
                [BINARY, "doing", "update_task", "job_1", "nonexistent_task", "success"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                errors.append(
                    f"Test5: update_task with nonexistent task_id expected non-zero exit, got 0. "
                    f"stdout={result.stdout.strip()}"
                )
            else:
                combined = result.stdout + result.stderr
                if not combined.strip():
                    errors.append(
                        "Test5: update_task with nonexistent task_id returned non-zero exit but no error message"
                    )
        except Exception as e:
            errors.append(f"Test5 exception: {str(e)}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    result = {
        "pass": len(errors) == 0,
        "errors": errors,
    }

    print(json.dumps(result))
    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
