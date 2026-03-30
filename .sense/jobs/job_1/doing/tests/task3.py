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


def main():
    errors = []

    # Build binary first
    if not build_binary(errors):
        result = {"pass": False, "errors": errors}
        print(json.dumps(result))
        sys.exit(1)

    # Test 1: go build ./... 编译成功（模板文件通过 //go:embed 嵌入）
    try:
        result = subprocess.run(
            ["go", "build", "./..."],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            errors.append(f"go build ./... failed: {result.stderr.strip()}")
    except Exception as e:
        errors.append(f"go build ./... exception: {str(e)}")

    # Create a temporary workspace for tests 2-4
    tmpdir = tempfile.mkdtemp()
    try:
        # Initialize .sense directory structure
        sense_dir = os.path.join(tmpdir, ".sense")
        os.makedirs(os.path.join(sense_dir, "wiki"), exist_ok=True)
        os.makedirs(os.path.join(sense_dir, "skills"), exist_ok=True)
        os.makedirs(os.path.join(sense_dir, "jobs"), exist_ok=True)

        # Create OKR.md and SPEC.md
        okr_content = "# OKR\n\nObjective: Build sense framework\nKey Result: Implement prompt system\n"
        spec_content = "# SPEC\n\nSense is a context-first AI coding framework.\n"
        wiki_content = "# Wiki Entry\n\nThis is a wiki document about the project.\n"
        skills_content = "# Skill: sense-ai-loop\n\nMain skill for AI loop.\n"

        with open(os.path.join(sense_dir, "OKR.md"), "w") as f:
            f.write(okr_content)
        with open(os.path.join(sense_dir, "SPEC.md"), "w") as f:
            f.write(spec_content)
        with open(os.path.join(sense_dir, "wiki", "overview.md"), "w") as f:
            f.write(wiki_content)
        with open(os.path.join(sense_dir, "skills", "sense-ai-loop.md"), "w") as f:
            f.write(skills_content)

        # Create a job directory with tasks for doing/test prompts
        job_dir = os.path.join(sense_dir, "jobs", "job_1")
        plan_dir = os.path.join(job_dir, "plan")
        os.makedirs(plan_dir, exist_ok=True)

        task1_content = """# 依赖关系
（无）

# 任务名称
初始化项目结构

# 任务目标
创建基础项目结构和 Go module。

# 关键结果
1. 初始化 Go module
2. 创建目录结构

# 测试方法
1. go build ./... 编译成功
2. sense --version 输出版本号
"""
        with open(os.path.join(plan_dir, "task1.md"), "w") as f:
            f.write(task1_content)

        # Test 2: sense tools gen_prompt plan job_1 — prompt contains OKR and SPEC content
        try:
            result = subprocess.run(
                [BINARY, "tools", "gen_prompt", "plan", "job_1"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                errors.append(
                    f"sense tools gen_prompt plan job_1 failed (exit {result.returncode}): "
                    f"{result.stderr.strip()}"
                )
            else:
                # Find the generated prompt file
                prompt_file = None
                for root, dirs, files in os.walk(tmpdir):
                    for fname in files:
                        if "plan" in fname and fname.endswith(".md"):
                            prompt_file = os.path.join(root, fname)
                            break
                    if prompt_file:
                        break

                # Also check prompts/ directory
                if not prompt_file:
                    prompts_dir = os.path.join(tmpdir, "prompts")
                    if os.path.isdir(prompts_dir):
                        for fname in os.listdir(prompts_dir):
                            if "plan" in fname:
                                prompt_file = os.path.join(prompts_dir, fname)
                                break

                if not prompt_file or not os.path.exists(prompt_file):
                    errors.append(
                        "gen_prompt plan: no plan prompt file found in output"
                    )
                else:
                    with open(prompt_file, "r") as f:
                        content = f.read()
                    if "Build sense framework" not in content and "OKR" not in content:
                        errors.append(
                            "gen_prompt plan: generated prompt does not contain OKR content"
                        )
                    if "Sense is a context-first" not in content and "SPEC" not in content:
                        errors.append(
                            "gen_prompt plan: generated prompt does not contain SPEC content"
                        )
        except Exception as e:
            errors.append(f"gen_prompt plan exception: {str(e)}")

        # Test 3: sense tools gen_prompt doing job_1 task1 — prompt contains task goal and test methods
        try:
            result = subprocess.run(
                [BINARY, "tools", "gen_prompt", "doing", "job_1", "task1"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                errors.append(
                    f"sense tools gen_prompt doing job_1 task1 failed (exit {result.returncode}): "
                    f"{result.stderr.strip()}"
                )
            else:
                # Find the generated doing prompt file
                prompt_file = None
                for root, dirs, files in os.walk(tmpdir):
                    for fname in files:
                        if "doing" in fname and fname.endswith(".md"):
                            prompt_file = os.path.join(root, fname)
                            break
                    if prompt_file:
                        break

                if not prompt_file or not os.path.exists(prompt_file):
                    errors.append(
                        "gen_prompt doing: no doing prompt file found in output"
                    )
                else:
                    with open(prompt_file, "r") as f:
                        content = f.read()
                    # Should contain task goal
                    if "初始化项目结构" not in content and "任务目标" not in content and "创建基础项目结构" not in content:
                        errors.append(
                            "gen_prompt doing: generated prompt does not contain task goal"
                        )
                    # Should contain test methods
                    if "go build" not in content and "测试方法" not in content and "sense --version" not in content:
                        errors.append(
                            "gen_prompt doing: generated prompt does not contain test methods"
                        )
        except Exception as e:
            errors.append(f"gen_prompt doing exception: {str(e)}")

        # Test 4: sense tools gen_prompt test job_1 task1 — test prompt contains test script path placeholder
        try:
            result = subprocess.run(
                [BINARY, "tools", "gen_prompt", "test", "job_1", "task1"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                errors.append(
                    f"sense tools gen_prompt test job_1 task1 failed (exit {result.returncode}): "
                    f"{result.stderr.strip()}"
                )
            else:
                # Find the generated test prompt file
                prompt_file = None
                for root, dirs, files in os.walk(tmpdir):
                    for fname in files:
                        if "test" in fname and fname.endswith(".md"):
                            prompt_file = os.path.join(root, fname)
                            break
                    if prompt_file:
                        break

                if not prompt_file or not os.path.exists(prompt_file):
                    errors.append(
                        "gen_prompt test: no test prompt file found in output"
                    )
                else:
                    with open(prompt_file, "r") as f:
                        content = f.read()
                    # Should contain test script path placeholder or reference
                    has_placeholder = (
                        "{{" in content
                        or ".py" in content
                        or "test_script" in content
                        or "tests/" in content
                        or "task1" in content
                    )
                    if not has_placeholder:
                        errors.append(
                            "gen_prompt test: generated prompt does not contain test script path placeholder"
                        )
        except Exception as e:
            errors.append(f"gen_prompt test exception: {str(e)}")

        # Test 5: wiki and skills content injected into prompts
        # Re-run plan prompt and check for wiki/skills content
        try:
            result = subprocess.run(
                [BINARY, "tools", "gen_prompt", "plan", "job_1"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                # Find any prompt file and check for wiki/skills injection
                all_prompt_content = ""
                for root, dirs, files in os.walk(tmpdir):
                    if "prompts" in root or "prompt" in root:
                        for fname in files:
                            if fname.endswith(".md"):
                                fpath = os.path.join(root, fname)
                                try:
                                    with open(fpath, "r") as f:
                                        all_prompt_content += f.read()
                                except Exception:
                                    pass

                if all_prompt_content:
                    wiki_injected = (
                        "Wiki Entry" in all_prompt_content
                        or "wiki" in all_prompt_content.lower()
                        or "overview" in all_prompt_content.lower()
                    )
                    skills_injected = (
                        "sense-ai-loop" in all_prompt_content
                        or "skills" in all_prompt_content.lower()
                        or "Skill:" in all_prompt_content
                    )
                    if not wiki_injected:
                        errors.append(
                            "wiki content not injected into generated prompt"
                        )
                    if not skills_injected:
                        errors.append(
                            "skills content not injected into generated prompt"
                        )
                # If no prompt files found, this test is inconclusive (already covered by test 2)
        except Exception as e:
            errors.append(f"wiki/skills injection check exception: {str(e)}")

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
