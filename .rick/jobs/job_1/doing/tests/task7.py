#!/usr/bin/env python3
import json
import sys
import os
import subprocess

SENSE_BIN = '/Users/sunquan/ai_coding/CODING/sense/bin/sense'
PROJECT_ROOT = '/Users/sunquan/ai_coding/CODING/sense'


def run(cmd, cwd=None, input_text=None):
    """Run a command, return (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=cwd or PROJECT_ROOT,
        input=input_text,
    )
    return result.returncode, result.stdout, result.stderr


def main():
    errors = []

    # Test 1: mock_agent.py exists
    mock_agent_path = os.path.join(PROJECT_ROOT, 'tests', 'mock_agent', 'mock_agent.py')
    if not os.path.exists(mock_agent_path):
        errors.append(f'tests/mock_agent/mock_agent.py does not exist at {mock_agent_path}')
    else:
        # Test 2: mock_agent.py --self-test outputs "OK: all self-tests passed"
        try:
            rc, stdout, stderr = run(['python3', mock_agent_path, '--self-test'])
            if 'OK: all self-tests passed' not in stdout:
                errors.append(
                    f'mock_agent.py --self-test did not output "OK: all self-tests passed"; '
                    f'stdout={stdout.strip()!r}, rc={rc}'
                )
        except Exception as e:
            errors.append(f'Failed to run mock_agent.py --self-test: {e}')

    # Test 3: integration_test.sh exists
    integration_test_path = os.path.join(PROJECT_ROOT, 'tests', 'integration_test.sh')
    if not os.path.exists(integration_test_path):
        errors.append(f'tests/integration_test.sh does not exist at {integration_test_path}')
    else:
        # Test 4: integration_test.sh exits 0
        try:
            rc, stdout, stderr = run(['bash', integration_test_path])
            if rc != 0:
                errors.append(
                    f'tests/integration_test.sh failed with exit code {rc}; '
                    f'stdout={stdout[-500:]!r}, stderr={stderr[-500:]!r}'
                )
        except Exception as e:
            errors.append(f'Failed to run tests/integration_test.sh: {e}')

        # Test 5: integration_test.sh covers dag + next_task scheduling loop (task1→task2→NONE)
        try:
            with open(integration_test_path, 'r') as f:
                content = f.read()
            if 'sense doing dag' not in content:
                errors.append('tests/integration_test.sh missing "sense doing dag" coverage')
            if 'sense doing next_task' not in content:
                errors.append('tests/integration_test.sh missing "sense doing next_task" coverage')
            # Check for NONE (end-of-schedule marker)
            if 'NONE' not in content:
                errors.append('tests/integration_test.sh missing NONE check for end-of-schedule')
        except Exception as e:
            errors.append(f'Failed to read tests/integration_test.sh: {e}')

    # Test 6: sense tools plan_check returns FAIL for plan_missing_section scenario
    # Create a temp workspace with a malformed plan file and verify plan_check fails
    import tempfile
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Init sense workspace
            rc, stdout, stderr = run([SENSE_BIN, 'init'], cwd=tmpdir)
            if rc != 0:
                errors.append(f'sense init failed in temp dir: {stderr.strip()!r}')
            else:
                # Create a job plan dir
                plan_dir = os.path.join(tmpdir, '.sense', 'jobs', 'job_1', 'plan')
                os.makedirs(plan_dir, exist_ok=True)
                # Write a task file missing required sections (e.g. missing 测试方法)
                bad_task = os.path.join(plan_dir, 'task1.md')
                with open(bad_task, 'w') as f:
                    f.write('# 依赖关系\n（无）\n\n# 任务名称\nTest Task\n\n# 任务目标\nGoal\n\n# 关键结果\n- KR1\n')
                    # Intentionally omit "# 测试方法" section

                rc, stdout, stderr = run([SENSE_BIN, 'tools', 'plan_check', 'job_1'], cwd=tmpdir)
                combined = stdout + stderr
                if rc == 0:
                    errors.append(
                        'sense tools plan_check should return FAIL for plan_missing_section '
                        f'but returned exit code 0; output={combined.strip()!r}'
                    )
                elif 'FAIL' not in combined and '测试方法' not in combined:
                    errors.append(
                        f'sense tools plan_check output does not mention FAIL or missing section; '
                        f'output={combined.strip()!r}'
                    )
    except Exception as e:
        errors.append(f'plan_check missing-section test raised exception: {e}')

    # Test 7: sense tools doing_check returns FAIL for zombie task and auto-recovers (reset to pending)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Init sense workspace
            rc, stdout, stderr = run([SENSE_BIN, 'init'], cwd=tmpdir)
            if rc != 0:
                errors.append(f'sense init failed in temp dir: {stderr.strip()!r}')
            else:
                # Create doing dir with a tasks.json containing a running (zombie) task
                doing_dir = os.path.join(tmpdir, '.sense', 'jobs', 'job_1', 'doing')
                os.makedirs(doing_dir, exist_ok=True)
                zombie_tasks = {
                    "version": "1.0",
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": "2026-01-01T00:00:00Z",
                    "tasks": [
                        {
                            "task_id": "task1",
                            "task_name": "Zombie Task",
                            "task_file": "task1.md",
                            "status": "running",
                            "dependencies": None,
                            "attempts": 0,
                            "created_at": "2026-01-01T00:00:00Z",
                            "updated_at": "2026-01-01T00:00:00Z"
                        }
                    ]
                }
                tasks_json_path = os.path.join(doing_dir, 'tasks.json')
                with open(tasks_json_path, 'w') as f:
                    json.dump(zombie_tasks, f)

                # doing_check should detect the zombie and return FAIL
                rc, stdout, stderr = run([SENSE_BIN, 'tools', 'doing_check', 'job_1'], cwd=tmpdir)
                combined = stdout + stderr
                if rc == 0:
                    errors.append(
                        'sense tools doing_check should return FAIL for zombie task '
                        f'but returned exit code 0; output={combined.strip()!r}'
                    )
                elif 'FAIL' not in combined and 'zombie' not in combined.lower():
                    errors.append(
                        f'sense tools doing_check output does not mention FAIL or zombie; '
                        f'output={combined.strip()!r}'
                    )

                # Auto-recovery: reset zombie task to pending via update_task
                try:
                    rc2, stdout2, stderr2 = run(
                        [SENSE_BIN, 'doing', 'update_task', 'job_1', 'task1', 'pending'],
                        cwd=tmpdir
                    )
                    if rc2 != 0:
                        errors.append(
                            f'sense doing update_task failed to reset zombie to pending: '
                            f'{(stdout2 + stderr2).strip()!r}'
                        )
                    else:
                        # After reset, doing_check should pass
                        rc3, stdout3, stderr3 = run(
                            [SENSE_BIN, 'tools', 'doing_check', 'job_1'],
                            cwd=tmpdir
                        )
                        if rc3 != 0:
                            errors.append(
                                f'sense tools doing_check should PASS after zombie reset to pending, '
                                f'but got exit code {rc3}; output={(stdout3+stderr3).strip()!r}'
                            )
                except Exception as e:
                    errors.append(f'Auto-recovery (update_task) raised exception: {e}')
    except Exception as e:
        errors.append(f'doing_check zombie test raised exception: {e}')

    result = {
        'pass': len(errors) == 0,
        'errors': errors
    }

    print(json.dumps(result))
    sys.exit(0 if result['pass'] else 1)


if __name__ == '__main__':
    main()
