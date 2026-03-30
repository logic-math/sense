# SPEC — sense 项目编码规范

## 语言与模块
- **语言**：Go（module: `github.com/sunquan/sense`，go 1.25+）
- **CLI 框架**：cobra（`github.com/spf13/cobra`）
- **包结构**：
  - `cmd/sense/main.go`：入口
  - `internal/cmd/`：cobra 子命令（doing、job、learning、tools、init、root）
  - `internal/workspace/`：`.sense/` 目录管理
  - `internal/parser/`：task.md 解析
  - `internal/executor/`：DAG 调度、tasks.json 管理
  - `internal/prompt/`：prompt 模板渲染

## task.md 格式规范
每个 task.md 必须包含以下五个 section（`# ` 开头）：
```
# 依赖关系
（无）或 task1, task2

# 任务名称
简短描述

# 任务目标
详细说明要做什么

# 关键结果
1. 可验证的产出物

# 测试方法
1. 如何验证
```

## tasks.json 格式规范
```json
{
  "version": "1.0",
  "created_at": "...",
  "updated_at": "...",
  "tasks": [
    {
      "task_id": "task1",
      "task_name": "...",
      "task_file": "task1.md",
      "status": "pending|running|success|failed",
      "dependencies": [],
      "attempts": 0,
      "commit_hash": "",
      "created_at": "...",
      "updated_at": "..."
    }
  ]
}
```

## 文件写入规范
- tasks.json 写入必须原子化（先写 `.tmp`，再 `rename`）
- 所有写操作支持幂等

## 测试规范
- 每个 task 对应一个 Python 测试脚本（`doing/tests/{task_id}.py`）
- 测试脚本输出 JSON：`{"pass": true/false, "errors": [...]}`
- 集成测试脚本：`tests/integration_test.sh`，CI 环境无需 claude 命令

## prompt 模板规范
- 模板文件位于 `internal/prompt/templates/*.md`
- 通过 `//go:embed` 嵌入二进制
- 变量使用 `{{variable}}` 语法
- 所有 prompt 自动注入 OKR、SPEC、wiki、skills 上下文

## check 命令输出规范
- 默认输出：`PASS` 或 `FAIL: <reason>`，退出码 0/1
- `--json` flag：`{"pass": true/false, "errors": [...]}`

## Git 提交规范
- task 粒度提交：`feat({task_id}): {task_name}`
- 每个 task 完成后立即 commit，支持回滚
