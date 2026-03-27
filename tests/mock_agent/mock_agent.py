#!/usr/bin/env python3
"""
mock_agent.py - Simulates sense-ai-loop sub-agent file system operations.

Usage:
    MOCK_SCENARIO=<scenario> python3 mock_agent.py <doing_dir_or_target_dir>
    python3 mock_agent.py --self-test

Scenarios (set via MOCK_SCENARIO env var):
    plan_success          - Create valid task1.md, task2.md in plan dir
    plan_missing_section  - Create task.md missing required sections
    plan_circular_dep     - Create task1.md, task2.md with circular dependency
    doing_success         - Create doing1.md worklog in doing/task1/ dir
    test_success          - Create test1.py that outputs {"pass": true, "errors": []}
    test_fail             - Create test1.py that outputs {"pass": false, "errors": ["assertion failed"]}
    learning_success      - Create README.md, wiki/arch.md, skills/check.py in learning dir
"""

import os
import sys
import json
import tempfile
import subprocess


VALID_TASK_TEMPLATE = """\
# 依赖关系
{deps}

# 任务名称
{name}

# 任务目标
{goal}

# 关键结果
- KR1: {kr}

# 测试方法
运行 `python3 tests/test_{task_id}.py`，验证输出 `{{"pass": true, "errors": []}}`
"""


def scenario_plan_success(target_dir):
    """Create valid task1.md and task2.md in target_dir (plan directory)."""
    os.makedirs(target_dir, exist_ok=True)

    task1 = VALID_TASK_TEMPLATE.format(
        deps="（无）",
        name="初始化项目",
        goal="创建项目基础结构",
        kr="项目目录已创建",
        task_id="task1",
    )
    with open(os.path.join(target_dir, "task1.md"), "w") as f:
        f.write(task1)

    task2 = VALID_TASK_TEMPLATE.format(
        deps="task1",
        name="实现核心功能",
        goal="实现主要业务逻辑",
        kr="功能测试通过",
        task_id="task2",
    )
    with open(os.path.join(target_dir, "task2.md"), "w") as f:
        f.write(task2)


def scenario_plan_missing_section(target_dir):
    """Create task.md missing required sections (no 测试方法)."""
    os.makedirs(target_dir, exist_ok=True)
    content = "# 依赖关系\n（无）\n\n# 任务名称\nTest Task\n\n# 任务目标\nGoal\n\n# 关键结果\n- KR1\n"
    # Intentionally omit "# 测试方法"
    with open(os.path.join(target_dir, "task1.md"), "w") as f:
        f.write(content)


def scenario_plan_circular_dep(target_dir):
    """Create task1.md and task2.md with circular dependency."""
    os.makedirs(target_dir, exist_ok=True)

    task1 = VALID_TASK_TEMPLATE.format(
        deps="task2",
        name="任务一",
        goal="目标一",
        kr="结果一",
        task_id="task1",
    )
    with open(os.path.join(target_dir, "task1.md"), "w") as f:
        f.write(task1)

    task2 = VALID_TASK_TEMPLATE.format(
        deps="task1",
        name="任务二",
        goal="目标二",
        kr="结果二",
        task_id="task2",
    )
    with open(os.path.join(target_dir, "task2.md"), "w") as f:
        f.write(task2)


def scenario_doing_success(target_dir):
    """Create doing1.md worklog in target_dir."""
    os.makedirs(target_dir, exist_ok=True)
    content = """\
## task1: 实现核心功能

**分析过程 (Analysis)**:
- 阅读了现有代码结构
- 确定了实现方案

**实现步骤 (Implementation)**:
1. 创建了主要模块
2. 实现了核心逻辑

**遇到的问题 (Issues)**:
- 无

**验证结果 (Verification)**:
- 测试命令：`python3 tests/test_task1.py`
- 测试输出：
  ```
  {"pass": true, "errors": []}
  ```
- 结论：✅ 通过
"""
    with open(os.path.join(target_dir, "doing1.md"), "w") as f:
        f.write(content)


def scenario_test_success(target_dir):
    """Create test1.py that outputs {"pass": true, "errors": []}."""
    os.makedirs(target_dir, exist_ok=True)
    content = """\
#!/usr/bin/env python3
import json
import sys

result = {"pass": True, "errors": []}
print(json.dumps(result))
sys.exit(0)
"""
    with open(os.path.join(target_dir, "test1.py"), "w") as f:
        f.write(content)


def scenario_test_fail(target_dir):
    """Create test1.py that outputs {"pass": false, "errors": ["assertion failed"]}."""
    os.makedirs(target_dir, exist_ok=True)
    content = """\
#!/usr/bin/env python3
import json
import sys

result = {"pass": False, "errors": ["assertion failed"]}
print(json.dumps(result))
sys.exit(1)
"""
    with open(os.path.join(target_dir, "test1.py"), "w") as f:
        f.write(content)


def scenario_learning_success(target_dir):
    """Create README.md, wiki/arch.md, skills/check.py in target_dir (learning dir)."""
    os.makedirs(target_dir, exist_ok=True)
    os.makedirs(os.path.join(target_dir, "wiki"), exist_ok=True)
    os.makedirs(os.path.join(target_dir, "skills"), exist_ok=True)

    readme = """\
# Learning Summary

## 项目概述
本次迭代实现了核心功能模块。

## 关键决策
- 使用模块化架构
- 最小化外部依赖

## 经验总结
- 先写测试，再实现功能
"""
    with open(os.path.join(target_dir, "README.md"), "w") as f:
        f.write(readme)

    arch = """\
# 架构设计

## 模块划分
- core: 核心业务逻辑
- utils: 工具函数

## 数据流
请求 → 处理 → 响应
"""
    with open(os.path.join(target_dir, "wiki", "arch.md"), "w") as f:
        f.write(arch)

    check_skill = """\
#!/usr/bin/env python3
\"\"\"check.py - 验证项目健康状态的 skill。\"\"\"
import os
import sys


def check_project(root_dir):
    \"\"\"Check that the project structure is valid.\"\"\"
    errors = []
    sense_dir = os.path.join(root_dir, ".sense")
    if not os.path.isdir(sense_dir):
        errors.append(f"Missing .sense directory at {sense_dir}")
    return errors


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    errs = check_project(root)
    if errs:
        for e in errs:
            print(f"ERROR: {e}")
        sys.exit(1)
    print("OK")
"""
    with open(os.path.join(target_dir, "skills", "check.py"), "w") as f:
        f.write(check_skill)


SCENARIOS = {
    "plan_success": scenario_plan_success,
    "plan_missing_section": scenario_plan_missing_section,
    "plan_circular_dep": scenario_plan_circular_dep,
    "doing_success": scenario_doing_success,
    "test_success": scenario_test_success,
    "test_fail": scenario_test_fail,
    "learning_success": scenario_learning_success,
}


def run_scenario(scenario, target_dir):
    if scenario not in SCENARIOS:
        print(f"ERROR: Unknown scenario {scenario!r}. Valid: {list(SCENARIOS)}", file=sys.stderr)
        sys.exit(1)
    SCENARIOS[scenario](target_dir)


# ---------------------------------------------------------------------------
# Self-test logic
# ---------------------------------------------------------------------------

def self_test():
    errors = []

    with tempfile.TemporaryDirectory() as tmpdir:
        # Test plan_success
        d = os.path.join(tmpdir, "plan_success")
        scenario_plan_success(d)
        for fname in ["task1.md", "task2.md"]:
            p = os.path.join(d, fname)
            if not os.path.exists(p):
                errors.append(f"plan_success: missing {fname}")
            else:
                content = open(p).read()
                for section in ["# 依赖关系", "# 任务名称", "# 任务目标", "# 关键结果", "# 测试方法"]:
                    if section not in content:
                        errors.append(f"plan_success: {fname} missing section {section!r}")

        # Test plan_missing_section
        d = os.path.join(tmpdir, "plan_missing")
        scenario_plan_missing_section(d)
        p = os.path.join(d, "task1.md")
        if not os.path.exists(p):
            errors.append("plan_missing_section: task1.md not created")
        else:
            content = open(p).read()
            if "# 测试方法" in content:
                errors.append("plan_missing_section: task1.md should NOT have 测试方法 section")

        # Test plan_circular_dep
        d = os.path.join(tmpdir, "plan_circular")
        scenario_plan_circular_dep(d)
        for fname in ["task1.md", "task2.md"]:
            if not os.path.exists(os.path.join(d, fname)):
                errors.append(f"plan_circular_dep: missing {fname}")
        # task1 should depend on task2 (circular)
        c1 = open(os.path.join(d, "task1.md")).read()
        c2 = open(os.path.join(d, "task2.md")).read()
        # Check the 依赖关系 section contains the dep (without leading "- ")
        dep_section_c1 = c1.split("# 依赖关系")[1].split("#")[0] if "# 依赖关系" in c1 else ""
        dep_section_c2 = c2.split("# 依赖关系")[1].split("#")[0] if "# 依赖关系" in c2 else ""
        if "task2" not in dep_section_c1:
            errors.append("plan_circular_dep: task1.md should depend on task2")
        if "task1" not in dep_section_c2:
            errors.append("plan_circular_dep: task2.md should depend on task1")

        # Test doing_success
        d = os.path.join(tmpdir, "doing_success")
        scenario_doing_success(d)
        p = os.path.join(d, "doing1.md")
        if not os.path.exists(p):
            errors.append("doing_success: doing1.md not created")
        else:
            content = open(p).read()
            if "分析过程" not in content:
                errors.append("doing_success: doing1.md missing 分析过程 section")

        # Test test_success
        d = os.path.join(tmpdir, "test_success")
        scenario_test_success(d)
        p = os.path.join(d, "test1.py")
        if not os.path.exists(p):
            errors.append("test_success: test1.py not created")
        else:
            result = subprocess.run(["python3", p], capture_output=True, text=True)
            try:
                data = json.loads(result.stdout)
                if not data.get("pass"):
                    errors.append(f"test_success: test1.py output pass=false: {result.stdout!r}")
                if data.get("errors"):
                    errors.append(f"test_success: test1.py output non-empty errors: {data['errors']}")
            except json.JSONDecodeError:
                errors.append(f"test_success: test1.py output not valid JSON: {result.stdout!r}")

        # Test test_fail
        d = os.path.join(tmpdir, "test_fail")
        scenario_test_fail(d)
        p = os.path.join(d, "test1.py")
        if not os.path.exists(p):
            errors.append("test_fail: test1.py not created")
        else:
            result = subprocess.run(["python3", p], capture_output=True, text=True)
            try:
                data = json.loads(result.stdout)
                if data.get("pass"):
                    errors.append("test_fail: test1.py should output pass=false")
                if "assertion failed" not in data.get("errors", []):
                    errors.append(f"test_fail: expected 'assertion failed' in errors: {data.get('errors')}")
            except json.JSONDecodeError:
                errors.append(f"test_fail: test1.py output not valid JSON: {result.stdout!r}")

        # Test learning_success
        d = os.path.join(tmpdir, "learning_success")
        scenario_learning_success(d)
        for rel in ["README.md", os.path.join("wiki", "arch.md"), os.path.join("skills", "check.py")]:
            p = os.path.join(d, rel)
            if not os.path.exists(p):
                errors.append(f"learning_success: missing {rel}")
        # Verify check.py is valid Python
        check_py = os.path.join(d, "skills", "check.py")
        if os.path.exists(check_py):
            result = subprocess.run(
                ["python3", "-m", "py_compile", check_py],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                errors.append(f"learning_success: check.py syntax error: {result.stderr}")

    if errors:
        for e in errors:
            print(f"FAIL: {e}")
        sys.exit(1)
    else:
        print("OK: all self-tests passed")
        sys.exit(0)


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--self-test":
        self_test()
        return

    scenario = os.environ.get("MOCK_SCENARIO", "")
    if not scenario:
        print("ERROR: MOCK_SCENARIO environment variable not set", file=sys.stderr)
        print(f"Valid scenarios: {list(SCENARIOS)}", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) < 2:
        print("ERROR: target directory argument required", file=sys.stderr)
        sys.exit(1)

    target_dir = sys.argv[1]
    run_scenario(scenario, target_dir)
    print(f"OK: scenario {scenario!r} applied to {target_dir}")


if __name__ == "__main__":
    main()
