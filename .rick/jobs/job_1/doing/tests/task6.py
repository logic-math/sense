#!/usr/bin/env python3
import json
import sys
import os
import subprocess

def main():
    errors = []

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))

    # Test 1: 验证主控 SKILL.md 存在
    main_skill = os.path.join(project_root, 'skills', 'sense-ai-loop', 'SKILL.md')
    if not os.path.exists(main_skill):
        errors.append(f'skills/sense-ai-loop/SKILL.md does not exist')
    else:
        try:
            with open(main_skill, 'r') as f:
                content = f.read()

            # Test 2: 验证 frontmatter 格式合法（name、description 字段存在）
            if 'name:' not in content:
                errors.append('skills/sense-ai-loop/SKILL.md missing "name:" in frontmatter')
            if 'description:' not in content:
                errors.append('skills/sense-ai-loop/SKILL.md missing "description:" in frontmatter')

            # Test 3: 验证主控 skill 中包含关键命令引用
            if 'sense doing dag' not in content:
                errors.append('skills/sense-ai-loop/SKILL.md missing "sense doing dag" command reference')
            if 'sense doing next_task' not in content:
                errors.append('skills/sense-ai-loop/SKILL.md missing "sense doing next_task" command reference')
            if 'sense tools doing_check' not in content:
                errors.append('skills/sense-ai-loop/SKILL.md missing "sense tools doing_check" command reference')

        except Exception as e:
            errors.append(f'Failed to read skills/sense-ai-loop/SKILL.md: {str(e)}')

    # Test 4: 验证 plan 子 skill 文件存在且包含输入/输出规范
    plan_skill = os.path.join(project_root, 'skills', 'sense-ai-loop', 'skills', 'plan.md')
    if not os.path.exists(plan_skill):
        errors.append('skills/sense-ai-loop/skills/plan.md does not exist')
    else:
        try:
            with open(plan_skill, 'r') as f:
                content = f.read()
            has_io = ('输入' in content or 'input' in content.lower() or 'Input' in content) and \
                     ('输出' in content or 'output' in content.lower() or 'Output' in content)
            if not has_io:
                errors.append('skills/sense-ai-loop/skills/plan.md missing input/output specification')
        except Exception as e:
            errors.append(f'Failed to read skills/sense-ai-loop/skills/plan.md: {str(e)}')

    # Test 5: 验证 doing 子 skill 文件存在且包含输入/输出规范
    doing_skill = os.path.join(project_root, 'skills', 'sense-ai-loop', 'skills', 'doing.md')
    if not os.path.exists(doing_skill):
        errors.append('skills/sense-ai-loop/skills/doing.md does not exist')
    else:
        try:
            with open(doing_skill, 'r') as f:
                content = f.read()
            has_io = ('输入' in content or 'input' in content.lower() or 'Input' in content) and \
                     ('输出' in content or 'output' in content.lower() or 'Output' in content)
            if not has_io:
                errors.append('skills/sense-ai-loop/skills/doing.md missing input/output specification')
        except Exception as e:
            errors.append(f'Failed to read skills/sense-ai-loop/skills/doing.md: {str(e)}')

    # Test 6: 验证 learning 子 skill 文件存在且包含输入/输出规范
    learning_skill = os.path.join(project_root, 'skills', 'sense-ai-loop', 'skills', 'learning.md')
    if not os.path.exists(learning_skill):
        errors.append('skills/sense-ai-loop/skills/learning.md does not exist')
    else:
        try:
            with open(learning_skill, 'r') as f:
                content = f.read()
            has_io = ('输入' in content or 'input' in content.lower() or 'Input' in content) and \
                     ('输出' in content or 'output' in content.lower() or 'Output' in content)
            if not has_io:
                errors.append('skills/sense-ai-loop/skills/learning.md missing input/output specification')
        except Exception as e:
            errors.append(f'Failed to read skills/sense-ai-loop/skills/learning.md: {str(e)}')

    # Test 7: 运行 ./install --list 验证 sense-ai-loop 出现在可安装列表中
    install_script = os.path.join(project_root, 'install')
    if not os.path.exists(install_script):
        errors.append('install script does not exist')
    else:
        try:
            result = subprocess.run(
                [install_script, '--list'],
                capture_output=True,
                text=True,
                cwd=project_root
            )
            if 'sense-ai-loop' not in result.stdout:
                errors.append(f'sense-ai-loop not found in ./install --list output')
        except Exception as e:
            errors.append(f'Failed to run ./install --list: {str(e)}')

    result = {
        'pass': len(errors) == 0,
        'errors': errors
    }

    print(json.dumps(result))
    sys.exit(0 if result['pass'] else 1)

if __name__ == '__main__':
    main()
