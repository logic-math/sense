#!/usr/bin/env bash
# integration_test.sh - End-to-end integration tests for the sense CLI.
# Runs without calling real Claude. Uses only the sense binary and mock_agent.py.
set -euo pipefail

SENSE_BIN="${SENSE_BIN:-$(cd "$(dirname "$0")/.." && pwd)/bin/sense}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MOCK_AGENT="$SCRIPT_DIR/mock_agent/mock_agent.py"

PASS=0
FAIL=0

pass() { echo "PASS: $1"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $1"; FAIL=$((FAIL + 1)); }

# ---------------------------------------------------------------------------
# Test 1: sense init creates .sense directory structure
# ---------------------------------------------------------------------------
TMPDIR1=$(mktemp -d)
trap 'rm -rf "$TMPDIR1"' EXIT

cd "$TMPDIR1"
"$SENSE_BIN" init > /dev/null 2>&1
if [ -d ".sense/wiki" ] && [ -d ".sense/skills" ] && [ -d ".sense/jobs" ]; then
    pass "sense init creates .sense directory structure"
else
    fail "sense init: missing expected directories"
fi

# ---------------------------------------------------------------------------
# Test 2: sense doing dag + next_task scheduling loop (task1→task2→NONE)
# ---------------------------------------------------------------------------
TMPDIR2=$(mktemp -d)
trap 'rm -rf "$TMPDIR2" "$TMPDIR1"' EXIT

cd "$TMPDIR2"
"$SENSE_BIN" init > /dev/null 2>&1

# Create plan directory with two tasks (task2 depends on task1)
mkdir -p .sense/jobs/job_1/plan

cat > .sense/jobs/job_1/plan/task1.md << 'EOF'
# 依赖关系
（无）

# 任务名称
初始化项目

# 任务目标
创建项目基础结构

# 关键结果
- KR1: 目录已创建

# 测试方法
运行 `python3 tests/test_task1.py`，验证输出 `{"pass": true, "errors": []}`
EOF

cat > .sense/jobs/job_1/plan/task2.md << 'EOF'
# 依赖关系
task1

# 任务名称
实现核心功能

# 任务目标
实现主要业务逻辑

# 关键结果
- KR1: 功能测试通过

# 测试方法
运行 `python3 tests/test_task2.py`，验证输出 `{"pass": true, "errors": []}`
EOF

# Generate DAG / tasks.json
"$SENSE_BIN" doing dag job_1 > /dev/null 2>&1
if [ -f ".sense/jobs/job_1/doing/tasks.json" ]; then
    pass "sense doing dag generates tasks.json"
else
    fail "sense doing dag: tasks.json not created"
fi

# Scheduling loop: task1 → task2 → NONE
NEXT=$("$SENSE_BIN" doing next_task job_1 2>/dev/null)
if [ "$NEXT" = "task1" ]; then
    pass "sense doing next_task returns task1 first"
else
    fail "sense doing next_task: expected task1, got '$NEXT'"
fi

# Mark task1 running then success
"$SENSE_BIN" doing update_task job_1 task1 running > /dev/null 2>&1
"$SENSE_BIN" doing update_task job_1 task1 success > /dev/null 2>&1

NEXT=$("$SENSE_BIN" doing next_task job_1 2>/dev/null)
if [ "$NEXT" = "task2" ]; then
    pass "sense doing next_task returns task2 after task1 completes"
else
    fail "sense doing next_task: expected task2 after task1 done, got '$NEXT'"
fi

# Mark task2 success
"$SENSE_BIN" doing update_task job_1 task2 running > /dev/null 2>&1
"$SENSE_BIN" doing update_task job_1 task2 success > /dev/null 2>&1

NEXT=$("$SENSE_BIN" doing next_task job_1 2>/dev/null)
if [ "$NEXT" = "NONE" ]; then
    pass "sense doing next_task returns NONE when all tasks done"
else
    fail "sense doing next_task: expected NONE after all tasks done, got '$NEXT'"
fi

# ---------------------------------------------------------------------------
# Test 3: sense tools plan_check PASS for valid plan
# ---------------------------------------------------------------------------
TMPDIR3=$(mktemp -d)
trap 'rm -rf "$TMPDIR3" "$TMPDIR2" "$TMPDIR1"' EXIT

cd "$TMPDIR3"
"$SENSE_BIN" init > /dev/null 2>&1
mkdir -p .sense/jobs/job_1/plan

python3 "$MOCK_AGENT" --self-test > /dev/null 2>&1
MOCK_PLAN_DIR=$(mktemp -d)
MOCK_SCENARIO=plan_success python3 "$MOCK_AGENT" "$MOCK_PLAN_DIR" > /dev/null 2>&1
cp "$MOCK_PLAN_DIR"/*.md .sense/jobs/job_1/plan/
rm -rf "$MOCK_PLAN_DIR"

if "$SENSE_BIN" tools plan_check job_1 > /dev/null 2>&1; then
    pass "sense tools plan_check PASS for valid plan"
else
    fail "sense tools plan_check: should PASS for valid plan"
fi

# ---------------------------------------------------------------------------
# Test 4: sense tools plan_check FAIL for plan_missing_section
# ---------------------------------------------------------------------------
TMPDIR4=$(mktemp -d)
trap 'rm -rf "$TMPDIR4" "$TMPDIR3" "$TMPDIR2" "$TMPDIR1"' EXIT

cd "$TMPDIR4"
"$SENSE_BIN" init > /dev/null 2>&1
mkdir -p .sense/jobs/job_1/plan

MOCK_MISSING_DIR=$(mktemp -d)
MOCK_SCENARIO=plan_missing_section python3 "$MOCK_AGENT" "$MOCK_MISSING_DIR" > /dev/null 2>&1
cp "$MOCK_MISSING_DIR"/*.md .sense/jobs/job_1/plan/
rm -rf "$MOCK_MISSING_DIR"

if ! "$SENSE_BIN" tools plan_check job_1 > /dev/null 2>&1; then
    pass "sense tools plan_check FAIL for plan_missing_section"
else
    fail "sense tools plan_check: should FAIL for plan_missing_section"
fi

# ---------------------------------------------------------------------------
# Test 5: sense tools doing_check FAIL for zombie task
# ---------------------------------------------------------------------------
TMPDIR5=$(mktemp -d)
trap 'rm -rf "$TMPDIR5" "$TMPDIR4" "$TMPDIR3" "$TMPDIR2" "$TMPDIR1"' EXIT

cd "$TMPDIR5"
"$SENSE_BIN" init > /dev/null 2>&1
mkdir -p .sense/jobs/job_1/doing

cat > .sense/jobs/job_1/doing/tasks.json << 'EOF'
{
  "version": "1.0",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z",
  "tasks": [
    {
      "task_id": "task1",
      "task_name": "Zombie Task",
      "task_file": "task1.md",
      "status": "running",
      "dependencies": null,
      "attempts": 0,
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z"
    }
  ]
}
EOF

OUTPUT=$("$SENSE_BIN" tools doing_check job_1 2>&1 || true)
if echo "$OUTPUT" | grep -qi "zombie\|FAIL"; then
    pass "sense tools doing_check FAIL for zombie task"
else
    fail "sense tools doing_check: should report zombie task; got: $OUTPUT"
fi

# Auto-recovery: reset zombie to pending
"$SENSE_BIN" doing update_task job_1 task1 pending > /dev/null 2>&1
if "$SENSE_BIN" tools doing_check job_1 > /dev/null 2>&1; then
    pass "sense tools doing_check PASS after zombie reset to pending"
else
    fail "sense tools doing_check: should PASS after zombie reset to pending"
fi

# ---------------------------------------------------------------------------
# Test 6: sense learning merge copies wiki/skills files
# ---------------------------------------------------------------------------
TMPDIR6=$(mktemp -d)
trap 'rm -rf "$TMPDIR6" "$TMPDIR5" "$TMPDIR4" "$TMPDIR3" "$TMPDIR2" "$TMPDIR1"' EXIT

cd "$TMPDIR6"
"$SENSE_BIN" init > /dev/null 2>&1

# Create learning dir with wiki/skills content
mkdir -p .sense/jobs/job_1/learning/wiki
mkdir -p .sense/jobs/job_1/learning/skills

echo "# Arch" > .sense/jobs/job_1/learning/wiki/arch.md
echo "#!/usr/bin/env python3\nprint('ok')" > .sense/jobs/job_1/learning/skills/check.py
echo "# Summary" > .sense/jobs/job_1/learning/README.md

"$SENSE_BIN" learning merge job_1 > /dev/null 2>&1
if [ -f ".sense/wiki/arch.md" ] && [ -f ".sense/skills/check.py" ]; then
    pass "sense learning merge copies wiki and skills files"
else
    fail "sense learning merge: expected .sense/wiki/arch.md and .sense/skills/check.py"
fi

# ---------------------------------------------------------------------------
# Test 7: parser 支持逗号分隔依赖（plan_comma_deps 场景）
# ---------------------------------------------------------------------------
TMPDIR7=$(mktemp -d)
trap 'rm -rf "$TMPDIR7" "$TMPDIR6" "$TMPDIR5" "$TMPDIR4" "$TMPDIR3" "$TMPDIR2" "$TMPDIR1"' EXIT

cd "$TMPDIR7"
"$SENSE_BIN" init > /dev/null 2>&1
mkdir -p .sense/jobs/job_1/plan

MOCK_COMMA_DIR=$(mktemp -d)
MOCK_SCENARIO=plan_comma_deps python3 "$MOCK_AGENT" "$MOCK_COMMA_DIR" > /dev/null 2>&1
cp "$MOCK_COMMA_DIR"/*.md .sense/jobs/job_1/plan/
rm -rf "$MOCK_COMMA_DIR"

if "$SENSE_BIN" doing dag job_1 > /dev/null 2>&1; then
    # Verify task3 has deps [task1, task2] in tasks.json
    DEPS=$(python3 -c "
import json, sys
with open('.sense/jobs/job_1/doing/tasks.json') as f:
    tj = json.load(f)
t3 = next((t for t in tj['tasks'] if t['task_id'] == 'task3'), None)
if t3 and t3['dependencies'] == ['task1', 'task2']:
    print('ok')
else:
    print('fail: ' + str(t3))
" 2>/dev/null)
    if [ "$DEPS" = "ok" ]; then
        pass "parser handles comma-separated deps (task1, task2)"
    else
        fail "parser comma deps: task3 deps wrong: $DEPS"
    fi
else
    fail "doing dag failed with comma-separated deps"
fi

# ---------------------------------------------------------------------------
# Test 8: update_task 位置参数形式（无 --status flag）
# ---------------------------------------------------------------------------
TMPDIR8=$(mktemp -d)
trap 'rm -rf "$TMPDIR8" "$TMPDIR7" "$TMPDIR6" "$TMPDIR5" "$TMPDIR4" "$TMPDIR3" "$TMPDIR2" "$TMPDIR1"' EXIT

cd "$TMPDIR8"
"$SENSE_BIN" init > /dev/null 2>&1
mkdir -p .sense/jobs/job_1/plan

cp "$TMPDIR7"/.sense/jobs/job_1/plan/*.md .sense/jobs/job_1/plan/ 2>/dev/null || true
# Use a simple single-task plan
cat > .sense/jobs/job_1/plan/task1.md << 'EOF'
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
EOF
"$SENSE_BIN" doing dag job_1 > /dev/null 2>&1

if "$SENSE_BIN" doing update_task job_1 task1 success --commit abc1234 > /dev/null 2>&1; then
    STATUS=$(python3 -c "
import json
with open('.sense/jobs/job_1/doing/tasks.json') as f:
    tj = json.load(f)
t = tj['tasks'][0]
print(t['status'] + '/' + t['commit_hash'])
" 2>/dev/null)
    if [ "$STATUS" = "success/abc1234" ]; then
        pass "update_task positional args with --commit works"
    else
        fail "update_task: wrong status/commit: $STATUS"
    fi
else
    fail "update_task positional form failed"
fi

# ---------------------------------------------------------------------------
# Test 9: gen_prompt 输出到 .sense/jobs/{job_id}/prompts/
# ---------------------------------------------------------------------------
TMPDIR9=$(mktemp -d)
trap 'rm -rf "$TMPDIR9" "$TMPDIR8" "$TMPDIR7" "$TMPDIR6" "$TMPDIR5" "$TMPDIR4" "$TMPDIR3" "$TMPDIR2" "$TMPDIR1"' EXIT

cd "$TMPDIR9"
"$SENSE_BIN" init > /dev/null 2>&1
mkdir -p .sense/jobs/job_1/plan

cat > .sense/jobs/job_1/plan/task1.md << 'EOF'
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
EOF

"$SENSE_BIN" tools gen_prompt plan job_1 > /dev/null 2>&1
if [ -f ".sense/jobs/job_1/prompts/plan_job_1.md" ]; then
    pass "gen_prompt outputs to .sense/jobs/{job_id}/prompts/"
else
    fail "gen_prompt: prompt not at .sense/jobs/job_1/prompts/plan_job_1.md"
fi
# Old path should NOT exist
if [ -d "prompts" ]; then
    fail "gen_prompt: old prompts/ dir at cwd root should not exist"
else
    pass "gen_prompt: no stray prompts/ dir at cwd root"
fi

# ---------------------------------------------------------------------------
# Test 10: gen_prompt learning 不含 {{job_summary}} 字面量
# ---------------------------------------------------------------------------
TMPDIR10=$(mktemp -d)
trap 'rm -rf "$TMPDIR10" "$TMPDIR9" "$TMPDIR8" "$TMPDIR7" "$TMPDIR6" "$TMPDIR5" "$TMPDIR4" "$TMPDIR3" "$TMPDIR2" "$TMPDIR1"' EXIT

cd "$TMPDIR10"
"$SENSE_BIN" init > /dev/null 2>&1
mkdir -p .sense/jobs/job_1/doing

cat > .sense/jobs/job_1/doing/tasks.json << 'EOF'
{
  "version": "1.0",
  "created_at": "2026-03-30T00:00:00Z",
  "updated_at": "2026-03-30T00:00:00Z",
  "tasks": [
    {
      "task_id": "task1",
      "task_name": "实现功能",
      "task_file": "task1.md",
      "status": "success",
      "dependencies": null,
      "attempts": 0,
      "commit_hash": "abc1234",
      "created_at": "2026-03-30T00:00:00Z",
      "updated_at": "2026-03-30T00:00:00Z"
    }
  ]
}
EOF

"$SENSE_BIN" tools gen_prompt learning job_1 > /dev/null 2>&1
PROMPT_FILE=".sense/jobs/job_1/prompts/learning_job_1.md"
if [ -f "$PROMPT_FILE" ]; then
    if grep -q '{{job_summary}}' "$PROMPT_FILE"; then
        fail "gen_prompt learning: {{job_summary}} literal still in prompt"
    else
        pass "gen_prompt learning: {{job_summary}} is replaced"
    fi
    if grep -q 'abc1234' "$PROMPT_FILE"; then
        pass "gen_prompt learning: tasks.json content injected into prompt"
    else
        fail "gen_prompt learning: tasks.json content not found in prompt"
    fi
else
    fail "gen_prompt learning: prompt file not created"
fi

# ---------------------------------------------------------------------------
# Test 11: learning_check PASS when README.md at job root
# ---------------------------------------------------------------------------
TMPDIR11=$(mktemp -d)
trap 'rm -rf "$TMPDIR11" "$TMPDIR10" "$TMPDIR9" "$TMPDIR8" "$TMPDIR7" "$TMPDIR6" "$TMPDIR5" "$TMPDIR4" "$TMPDIR3" "$TMPDIR2" "$TMPDIR1"' EXIT

cd "$TMPDIR11"
"$SENSE_BIN" init > /dev/null 2>&1

# Use learning_readme mock scenario: README.md at job root
MOCK_JOB_DIR=$(mktemp -d)
MOCK_SCENARIO=learning_readme python3 "$MOCK_AGENT" "$MOCK_JOB_DIR" > /dev/null 2>&1
mkdir -p .sense/jobs/job_1
cp -r "$MOCK_JOB_DIR"/. .sense/jobs/job_1/
rm -rf "$MOCK_JOB_DIR"

if "$SENSE_BIN" tools learning_check job_1 > /dev/null 2>&1; then
    pass "learning_check PASS when README.md is at job root"
else
    fail "learning_check: should PASS with README.md at job root"
fi

# Without README.md at job root → FAIL
rm -f .sense/jobs/job_1/README.md
if ! "$SENSE_BIN" tools learning_check job_1 > /dev/null 2>&1; then
    pass "learning_check FAIL when README.md missing from job root"
else
    fail "learning_check: should FAIL without README.md at job root"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "Results: $PASS passed, $FAIL failed"
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
