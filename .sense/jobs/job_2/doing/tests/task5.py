#!/usr/bin/env python3
"""task5 test: 集成验证 mock_agent + integration_test 覆盖所有 Bug 修复"""
import json, os, subprocess, sys

SENSE_BIN = os.environ.get("SENSE_BIN", os.path.expanduser("~/.local/bin/sense"))
PROJECT_ROOT = "/opt/meituan/dolphinfs_sunquan20/ai_coding/Coding/sense"
errors = []

def run(cmd, cwd=None, env=None):
    import os as _os
    e = dict(_os.environ)
    if env:
        e.update(env)
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd, env=e)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

# ── Case 1: mock_agent --self-test 通过 ───────────────────────────────────
rc, out, err = run(f"python3 {PROJECT_ROOT}/tests/mock_agent/mock_agent.py --self-test")
if rc != 0 or "OK: all self-tests passed" not in out:
    errors.append(f"Case1: mock_agent --self-test failed: {out} {err}")

# ── Case 2: integration_test.sh 全部通过 ─────────────────────────────────
rc, out, err = run(
    f"bash {PROJECT_ROOT}/tests/integration_test.sh",
    env={"SENSE_BIN": f"{PROJECT_ROOT}/bin/sense"}
)
if rc != 0:
    errors.append(f"Case2: integration_test.sh failed:\n{out}\n{err}")
else:
    # 确认新增的 5 个测试（Test 7-11）都出现在输出中
    for keyword in [
        "comma-separated deps",
        "update_task positional",
        "gen_prompt outputs to .sense/jobs",
        "job_summary}} is replaced",
        "learning_check PASS when README.md is at job root",
    ]:
        if keyword not in out:
            errors.append(f"Case2: expected test keyword not found: {keyword!r}")

# ── Case 3: FAIL 行数为 0 ─────────────────────────────────────────────────
if "FAIL:" in out:
    fail_lines = [l for l in out.splitlines() if l.startswith("FAIL:")]
    errors.append(f"Case3: integration_test has FAIL lines: {fail_lines}")

# ── Case 4: 总通过数 >= 18 ────────────────────────────────────────────────
pass_count = out.count("\nPASS:") + (1 if out.startswith("PASS:") else 0)
if pass_count < 18:
    errors.append(f"Case4: expected >= 18 PASS, got {pass_count}")

result = {"pass": len(errors) == 0, "errors": errors}
print(json.dumps(result, ensure_ascii=False, indent=2))
sys.exit(0 if result["pass"] else 1)
