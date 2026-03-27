#!/usr/bin/env python3
import json
import sys
import os
import subprocess
import tempfile
import shutil

PROJECT_ROOT = "/Users/sunquan/ai_coding/CODING/sense"


def main():
    errors = []

    # Test 1: go build ./... 编译成功
    try:
        result = subprocess.run(
            ["go", "build", "-o", "bin/sense", "./cmd/sense/..."],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            errors.append(f"go build failed: {result.stderr.strip()}")
    except Exception as e:
        errors.append(f"go build exception: {str(e)}")

    # Test 2: ./bin/sense --version 输出版本号
    binary = os.path.join(PROJECT_ROOT, "bin", "sense")
    try:
        result = subprocess.run(
            [binary, "--version"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            errors.append(f"./bin/sense --version failed (exit {result.returncode}): {result.stderr.strip()}")
        elif not result.stdout.strip():
            errors.append("./bin/sense --version produced no output")
    except Exception as e:
        errors.append(f"./bin/sense --version exception: {str(e)}")

    # Test 3: ./bin/sense init 在临时目录创建 .sense/ 结构
    tmpdir = tempfile.mkdtemp()
    try:
        result = subprocess.run(
            [binary, "init"],
            cwd=tmpdir,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            errors.append(f"./bin/sense init failed (exit {result.returncode}): {result.stderr.strip()}")
        else:
            sense_dir = os.path.join(tmpdir, ".sense")
            if not os.path.isdir(sense_dir):
                errors.append(f".sense/ directory not created by 'sense init'")
            else:
                expected_dirs = ["wiki", "skills", "jobs"]
                for d in expected_dirs:
                    full = os.path.join(sense_dir, d)
                    if not os.path.isdir(full):
                        errors.append(f".sense/{d}/ directory missing after 'sense init'")
                expected_files = ["OKR.md", "SPEC.md"]
                for f in expected_files:
                    full = os.path.join(sense_dir, f)
                    if not os.path.exists(full):
                        errors.append(f".sense/{f} file missing after 'sense init'")
    except Exception as e:
        errors.append(f"./bin/sense init exception: {str(e)}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    # Test 4: workspace.NextJobID() 逻辑验证（通过 Go test 或直接调用 sense 命令）
    # 用 go test 直接测试 workspace 包
    try:
        test_code = '''package workspace_test

import (
    "os"
    "path/filepath"
    "testing"
    "github.com/sunquan/sense/internal/workspace"
)

func TestNextJobID(t *testing.T) {
    dir := t.TempDir()
    jobsDir := filepath.Join(dir, "jobs")
    if err := os.MkdirAll(jobsDir, 0755); err != nil {
        t.Fatal(err)
    }

    // Empty jobs dir should return job_1
    id, err := workspace.NextJobID(dir)
    if err != nil {
        t.Fatalf("NextJobID on empty dir failed: %v", err)
    }
    if id != "job_1" {
        t.Errorf("expected job_1, got %s", id)
    }

    // Create job_1, should return job_2
    if err := os.MkdirAll(filepath.Join(jobsDir, "job_1"), 0755); err != nil {
        t.Fatal(err)
    }
    id, err = workspace.NextJobID(dir)
    if err != nil {
        t.Fatalf("NextJobID with job_1 failed: %v", err)
    }
    if id != "job_2" {
        t.Errorf("expected job_2, got %s", id)
    }
}
'''
        test_file = os.path.join(PROJECT_ROOT, "internal", "workspace", "nextjobid_rick_test.go")
        with open(test_file, "w") as f:
            f.write(test_code)

        result = subprocess.run(
            ["go", "test", "-run", "TestNextJobID", "-v", "./internal/workspace/..."],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        os.remove(test_file)

        if result.returncode != 0:
            errors.append(f"workspace.NextJobID test failed: {result.stdout.strip()} {result.stderr.strip()}")
    except Exception as e:
        errors.append(f"workspace.NextJobID test exception: {str(e)}")
        # cleanup if file exists
        test_file = os.path.join(PROJECT_ROOT, "internal", "workspace", "nextjobid_rick_test.go")
        if os.path.exists(test_file):
            os.remove(test_file)

    # Test 5: parser 能正确解析 task.md 的五个 section
    try:
        task1_md = os.path.join(PROJECT_ROOT, ".rick", "jobs", "job_1", "plan", "task1.md")
        if not os.path.exists(task1_md):
            errors.append(f"task1.md not found at {task1_md}")
        else:
            test_code = f'''package parser_test

import (
    "testing"
    "github.com/sunquan/sense/internal/parser"
)

func TestParseTask(t *testing.T) {{
    task, err := parser.ParseTaskFile("{task1_md}")
    if err != nil {{
        t.Fatalf("ParseTaskFile failed: %v", err)
    }}

    // 验证五个 section 存在
    if task.Name == "" {{
        t.Error("task.Name is empty")
    }}
    if task.Goal == "" {{
        t.Error("task.Goal is empty")
    }}
    if task.KeyResults == nil || len(task.KeyResults) == 0 {{
        t.Error("task.KeyResults is empty")
    }}
    if task.TestMethods == nil || len(task.TestMethods) == 0 {{
        t.Error("task.TestMethods is empty")
    }}

    // 验证 （无） 表示无依赖
    if len(task.Dependencies) != 0 {{
        t.Errorf("expected no dependencies, got: %v", task.Dependencies)
    }}
}}
'''
            test_file = os.path.join(PROJECT_ROOT, "internal", "parser", "task_rick_test.go")
            with open(test_file, "w") as f:
                f.write(test_code)

            result = subprocess.run(
                ["go", "test", "-run", "TestParseTask", "-v", "./internal/parser/..."],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
            )
            os.remove(test_file)

            if result.returncode != 0:
                errors.append(f"parser.ParseTaskFile test failed: {result.stdout.strip()} {result.stderr.strip()}")
    except Exception as e:
        errors.append(f"parser test exception: {str(e)}")
        test_file = os.path.join(PROJECT_ROOT, "internal", "parser", "task_rick_test.go")
        if os.path.exists(test_file):
            os.remove(test_file)

    result = {
        "pass": len(errors) == 0,
        "errors": errors,
    }

    print(json.dumps(result))
    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
