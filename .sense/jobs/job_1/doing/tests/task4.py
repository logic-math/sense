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


def make_valid_task_md():
    return """# 依赖关系
（无）

# 任务名称
测试任务

# 任务目标
这是一个测试任务。

# 关键结果
1. 完成测试

# 测试方法
1. 运行测试脚本
"""


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
        plan_dir = os.path.join(job_dir, "plan")
        doing_dir = os.path.join(job_dir, "doing")
        learning_dir = os.path.join(job_dir, "learning")
        skills_dir = os.path.join(learning_dir, "skills")

        os.makedirs(plan_dir, exist_ok=True)
        os.makedirs(doing_dir, exist_ok=True)
        os.makedirs(skills_dir, exist_ok=True)

        # Test 1: 创建合法的 plan 目录，运行 plan_check，验证退出码为 0 且输出 PASS
        try:
            with open(os.path.join(plan_dir, "task1.md"), "w") as f:
                f.write(make_valid_task_md())

            result = subprocess.run(
                [BINARY, "tools", "plan_check", "job_1"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                errors.append(
                    f"Test1: plan_check on valid plan dir expected exit 0, got {result.returncode}. "
                    f"stdout={result.stdout.strip()} stderr={result.stderr.strip()}"
                )
            else:
                combined = result.stdout + result.stderr
                if "PASS" not in combined.upper():
                    errors.append(
                        f"Test1: plan_check valid plan did not output PASS. "
                        f"stdout={result.stdout.strip()}"
                    )
        except Exception as e:
            errors.append(f"Test1 exception: {str(e)}")

        # Test 2: 创建缺少 `# 关键结果` section 的 task.md，运行 plan_check，验证退出码为 1 且输出包含 FAIL 原因
        try:
            bad_task_content = """# 依赖关系
（无）

# 任务名称
缺少关键结果的任务

# 任务目标
这个任务缺少关键结果 section。

# 测试方法
1. 运行测试
"""
            with open(os.path.join(plan_dir, "task_bad.md"), "w") as f:
                f.write(bad_task_content)

            result = subprocess.run(
                [BINARY, "tools", "plan_check", "job_1"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                errors.append(
                    f"Test2: plan_check on task missing '# 关键结果' expected exit 1, got 0. "
                    f"stdout={result.stdout.strip()}"
                )
            else:
                combined = result.stdout + result.stderr
                if "FAIL" not in combined.upper():
                    errors.append(
                        f"Test2: plan_check missing section did not output FAIL reason. "
                        f"stdout={result.stdout.strip()}"
                    )
        except Exception as e:
            errors.append(f"Test2 exception: {str(e)}")
        finally:
            # Remove bad task file to avoid affecting subsequent tests
            bad_task_path = os.path.join(plan_dir, "task_bad.md")
            if os.path.exists(bad_task_path):
                os.remove(bad_task_path)

        # Test 3: 创建含 zombie task（status=running）的 tasks.json，运行 doing_check，验证退出码为 1
        try:
            zombie_tasks = {
                "version": "1.0",
                "tasks": [
                    {
                        "task_id": "task1",
                        "task_name": "测试任务",
                        "status": "running",
                        "dependencies": None,
                        "attempts": 0,
                    }
                ],
            }
            with open(os.path.join(doing_dir, "tasks.json"), "w") as f:
                json.dump(zombie_tasks, f)

            result = subprocess.run(
                [BINARY, "tools", "doing_check", "job_1"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                errors.append(
                    f"Test3: doing_check with zombie task (status=running) expected exit 1, got 0. "
                    f"stdout={result.stdout.strip()}"
                )
        except Exception as e:
            errors.append(f"Test3 exception: {str(e)}")

        # Test 4: 创建含语法错误 Python 文件的 learning/skills/，运行 learning_check，验证退出码为 1
        try:
            # Create README.md for learning dir
            with open(os.path.join(learning_dir, "README.md"), "w") as f:
                f.write("# Learning\n\n执行摘要\n")

            # Create a Python file with syntax error
            with open(os.path.join(skills_dir, "bad_skill.py"), "w") as f:
                f.write("def broken(\n    # missing closing paren and body\n")

            result = subprocess.run(
                [BINARY, "tools", "learning_check", "job_1"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                errors.append(
                    f"Test4: learning_check with syntax-error Python file expected exit 1, got 0. "
                    f"stdout={result.stdout.strip()}"
                )
        except Exception as e:
            errors.append(f"Test4 exception: {str(e)}")

        # Test 5: 运行 plan_check --json，验证输出为合法 JSON（{"pass": true/false, "errors": [...]}）
        try:
            # Ensure only valid task exists in plan dir
            for fname in os.listdir(plan_dir):
                os.remove(os.path.join(plan_dir, fname))
            with open(os.path.join(plan_dir, "task1.md"), "w") as f:
                f.write(make_valid_task_md())

            result = subprocess.run(
                [BINARY, "tools", "plan_check", "job_1", "--json"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
            )
            stdout = result.stdout.strip()
            try:
                parsed = json.loads(stdout)
                if "pass" not in parsed:
                    errors.append(
                        f"Test5: plan_check --json output missing 'pass' field. got: {stdout}"
                    )
                if "errors" not in parsed:
                    errors.append(
                        f"Test5: plan_check --json output missing 'errors' field. got: {stdout}"
                    )
                if not isinstance(parsed.get("errors"), list):
                    errors.append(
                        f"Test5: plan_check --json 'errors' field is not a list. got: {stdout}"
                    )
            except json.JSONDecodeError as e:
                errors.append(
                    f"Test5: plan_check --json output is not valid JSON: {stdout!r}. error: {e}"
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
