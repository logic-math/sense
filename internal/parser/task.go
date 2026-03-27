package parser

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

// Task represents a parsed task.md file.
type Task struct {
	Dependencies []string
	Name         string
	Goal         string
	KeyResults   []string
	TestMethods  []string
}

// ParseTaskFile reads and parses a task.md file.
func ParseTaskFile(path string) (*Task, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("open %s: %w", path, err)
	}
	defer f.Close()

	sections := make(map[string][]string)
	var currentSection string

	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := scanner.Text()
		if strings.HasPrefix(line, "# ") {
			currentSection = strings.TrimPrefix(line, "# ")
			continue
		}
		if currentSection != "" {
			sections[currentSection] = append(sections[currentSection], line)
		}
	}
	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("scan %s: %w", path, err)
	}

	task := &Task{}

	// 依赖关系
	depLines := trimLines(sections["依赖关系"])
	for _, l := range depLines {
		if l == "（无）" || l == "(无)" {
			// no dependencies
			break
		}
		if l != "" {
			task.Dependencies = append(task.Dependencies, l)
		}
	}

	// 任务名称
	task.Name = strings.Join(trimLines(sections["任务名称"]), " ")
	task.Name = strings.TrimSpace(task.Name)

	// 任务目标
	task.Goal = strings.Join(trimLines(sections["任务目标"]), "\n")
	task.Goal = strings.TrimSpace(task.Goal)

	// 关键结果
	for _, l := range trimLines(sections["关键结果"]) {
		if l != "" {
			task.KeyResults = append(task.KeyResults, l)
		}
	}

	// 测试方法
	for _, l := range trimLines(sections["测试方法"]) {
		if l != "" {
			task.TestMethods = append(task.TestMethods, l)
		}
	}

	return task, nil
}

func trimLines(lines []string) []string {
	var result []string
	for _, l := range lines {
		result = append(result, strings.TrimSpace(l))
	}
	// strip leading/trailing empty lines
	start, end := 0, len(result)
	for start < end && result[start] == "" {
		start++
	}
	for end > start && result[end-1] == "" {
		end--
	}
	return result[start:end]
}
