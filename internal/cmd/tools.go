package cmd

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/spf13/cobra"
	"github.com/sunquan/sense/internal/executor"
	"github.com/sunquan/sense/internal/parser"
	"github.com/sunquan/sense/internal/prompt"
	"github.com/sunquan/sense/internal/workspace"
)

// checkResult holds the result of a check command.
type checkResult struct {
	Pass   bool     `json:"pass"`
	Errors []string `json:"errors"`
}

func (r *checkResult) output(jsonMode bool) {
	if jsonMode {
		data, _ := json.Marshal(r)
		fmt.Println(string(data))
		return
	}
	if r.Pass {
		fmt.Println("PASS")
	} else {
		fmt.Printf("FAIL: %s\n", strings.Join(r.Errors, "; "))
	}
}

func (r *checkResult) exitCode() int {
	if r.Pass {
		return 0
	}
	return 1
}

var toolsCmd = &cobra.Command{
	Use:   "tools",
	Short: "Utility tools for sense",
}

var genPromptCmd = &cobra.Command{
	Use:   "gen_prompt <phase> <job_id> [task_id]",
	Short: "Generate a prompt file for a given phase",
	Args:  cobra.RangeArgs(2, 3),
	RunE: func(cmd *cobra.Command, args []string) error {
		phase := args[0]
		jobID := args[1]
		taskID := ""
		if len(args) == 3 {
			taskID = args[2]
		}

		cwd, err := os.Getwd()
		if err != nil {
			return fmt.Errorf("get working directory: %w", err)
		}

		senseDir := workspace.GetSenseDir(cwd)
		ctx, err := prompt.LoadContext(senseDir)
		if err != nil {
			return fmt.Errorf("load context: %w", err)
		}

		vars := map[string]string{
			"job_id":  jobID,
			"task_id": taskID,
			"okr":     ctx.OKR,
			"spec":    ctx.SPEC,
			"wiki":    ctx.WikiContent(),
			"skills":  ctx.SkillsContent(),
		}

		// For task-specific phases, load task info
		if taskID != "" {
			planDir := workspace.GetJobPlanDir(cwd, jobID)
			taskFile := filepath.Join(planDir, taskID+".md")
			task, err := parser.ParseTaskFile(taskFile)
			if err != nil {
				return fmt.Errorf("parse task file %s: %w", taskFile, err)
			}
			vars["task_name"] = task.Name
			vars["task_goal"] = task.Goal
			vars["task_key_results"] = strings.Join(task.KeyResults, "\n")
			vars["task_test_methods"] = strings.Join(task.TestMethods, "\n")
			doingDir := workspace.GetJobDoingDir(cwd, jobID)
			vars["test_script_path"] = filepath.Join(doingDir, "tests", taskID+".py")
			vars["git_diff"] = "{{git_diff}}"
		}

		// For learning phase, inject job_summary from tasks.json + debug.md
		if phase == "learning" {
			vars["job_summary"] = buildJobSummary(cwd, jobID)
		}

		content, err := prompt.Build(phase, vars)
		if err != nil {
			return fmt.Errorf("build prompt: %w", err)
		}

		// Write to .sense/jobs/{job_id}/prompts/ directory
		promptsDir := workspace.GetJobPromptsDir(cwd, jobID)
		if err := os.MkdirAll(promptsDir, 0755); err != nil {
			return fmt.Errorf("create prompts dir: %w", err)
		}

		var filename string
		if taskID != "" {
			filename = fmt.Sprintf("%s_%s_%s.md", phase, jobID, taskID)
		} else {
			filename = fmt.Sprintf("%s_%s.md", phase, jobID)
		}

		outPath := filepath.Join(promptsDir, filename)
		if err := os.WriteFile(outPath, []byte(content), 0644); err != nil {
			return fmt.Errorf("write prompt file: %w", err)
		}

		fmt.Printf("Generated prompt: %s\n", outPath)
		return nil
	},
}

// buildJobSummary reads tasks.json and debug.md for a job and returns a summary string.
func buildJobSummary(root, jobID string) string {
	var sb strings.Builder

	doingDir := workspace.GetJobDoingDir(root, jobID)

	// tasks.json summary
	tasksPath := filepath.Join(doingDir, "tasks.json")
	if data, err := os.ReadFile(tasksPath); err == nil {
		sb.WriteString("## tasks.json\n\n```json\n")
		sb.Write(data)
		sb.WriteString("\n```\n\n")
	}

	// debug.md (optional)
	debugPath := filepath.Join(doingDir, "debug.md")
	if data, err := os.ReadFile(debugPath); err == nil {
		sb.WriteString("## debug.md\n\n")
		sb.Write(data)
		sb.WriteString("\n")
	}

	return sb.String()
}

var planCheckCmd = &cobra.Command{
	Use:   "plan_check <job_id>",
	Short: "Validate the plan directory for a job",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		jobID := args[0]
		jsonMode, _ := cmd.Flags().GetBool("json")

		cwd, err := os.Getwd()
		if err != nil {
			return err
		}
		planDir := workspace.GetJobPlanDir(cwd, jobID)

		res := &checkResult{Pass: true, Errors: []string{}}

		// Find task*.md files
		entries, err := os.ReadDir(planDir)
		if err != nil {
			res.Pass = false
			res.Errors = append(res.Errors, fmt.Sprintf("cannot read plan dir: %v", err))
			res.output(jsonMode)
			os.Exit(res.exitCode())
			return nil
		}

		var taskFiles []string
		for _, e := range entries {
			if !e.IsDir() && strings.HasPrefix(e.Name(), "task") && strings.HasSuffix(e.Name(), ".md") {
				taskFiles = append(taskFiles, e.Name())
			}
		}

		if len(taskFiles) == 0 {
			res.Pass = false
			res.Errors = append(res.Errors, "no task*.md files found in plan dir")
			res.output(jsonMode)
			os.Exit(res.exitCode())
			return nil
		}

		// Validate each task file and collect entries for DAG check
		requiredSections := []string{"依赖关系", "任务名称", "任务目标", "关键结果", "测试方法"}
		var dagEntries []executor.TaskEntry

		for _, fname := range taskFiles {
			taskPath := filepath.Join(planDir, fname)
			taskID := strings.TrimSuffix(fname, ".md")

			// Check sections by raw scan
			data, err := os.ReadFile(taskPath)
			if err != nil {
				res.Pass = false
				res.Errors = append(res.Errors, fmt.Sprintf("%s: cannot read: %v", fname, err))
				continue
			}
			content := string(data)
			for _, sec := range requiredSections {
				if !strings.Contains(content, "# "+sec) {
					res.Pass = false
					res.Errors = append(res.Errors, fmt.Sprintf("%s: missing section '# %s'", fname, sec))
				}
			}

			task, err := parser.ParseTaskFile(taskPath)
			if err != nil {
				res.Pass = false
				res.Errors = append(res.Errors, fmt.Sprintf("%s: parse error: %v", fname, err))
				continue
			}
			dagEntries = append(dagEntries, executor.TaskEntry{
				TaskID:   taskID,
				TaskFile: fname,
				Task:     task,
			})
		}

		// Check for cycles
		if len(dagEntries) > 0 {
			if _, err := executor.BuildDAG(dagEntries); err != nil {
				res.Pass = false
				res.Errors = append(res.Errors, fmt.Sprintf("dependency error: %v", err))
			}
		}

		res.output(jsonMode)
		os.Exit(res.exitCode())
		return nil
	},
}

var doingCheckCmd = &cobra.Command{
	Use:   "doing_check <job_id>",
	Short: "Validate the doing directory for a job",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		jobID := args[0]
		jsonMode, _ := cmd.Flags().GetBool("json")

		cwd, err := os.Getwd()
		if err != nil {
			return err
		}
		doingDir := workspace.GetJobDoingDir(cwd, jobID)

		res := &checkResult{Pass: true, Errors: []string{}}

		tj, err := executor.Load(doingDir)
		if err != nil {
			res.Pass = false
			res.Errors = append(res.Errors, fmt.Sprintf("tasks.json invalid: %v", err))
			res.output(jsonMode)
			os.Exit(res.exitCode())
			return nil
		}

		// Detect zombie tasks (status=running but process doesn't exist)
		// Since we can't know the PID, any running task is treated as a zombie.
		for _, t := range tj.Tasks {
			if t.Status == executor.StatusRunning {
				res.Pass = false
				res.Errors = append(res.Errors, fmt.Sprintf("zombie task detected: %s (status=running)", t.TaskID))
			}
		}

		res.output(jsonMode)
		os.Exit(res.exitCode())
		return nil
	},
}

var learningCheckCmd = &cobra.Command{
	Use:   "learning_check <job_id>",
	Short: "Validate the learning directory for a job",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		jobID := args[0]
		jsonMode, _ := cmd.Flags().GetBool("json")

		cwd, err := os.Getwd()
		if err != nil {
			return err
		}
		jobDir := filepath.Join(workspace.GetSenseDir(cwd), "jobs", jobID)
		learningDir := workspace.GetJobLearningDir(cwd, jobID)

		res := &checkResult{Pass: true, Errors: []string{}}

		// Check README.md exists at job root (not inside learning/)
		readmePath := filepath.Join(jobDir, "README.md")
		if _, err := os.Stat(readmePath); os.IsNotExist(err) {
			res.Pass = false
			res.Errors = append(res.Errors, fmt.Sprintf("%s not found", readmePath))
		}

		// Check Python files in learning/skills/ for syntax errors
		skillsDir := filepath.Join(learningDir, "skills")
		entries, err := os.ReadDir(skillsDir)
		if err != nil && !os.IsNotExist(err) {
			res.Pass = false
			res.Errors = append(res.Errors, fmt.Sprintf("cannot read skills dir: %v", err))
		} else if err == nil {
			for _, e := range entries {
				if e.IsDir() || !strings.HasSuffix(e.Name(), ".py") {
					continue
				}
				pyPath := filepath.Join(skillsDir, e.Name())
				out, err := exec.Command("python3", "-m", "py_compile", pyPath).CombinedOutput()
				if err != nil {
					res.Pass = false
					res.Errors = append(res.Errors, fmt.Sprintf("syntax error in %s: %s", e.Name(), strings.TrimSpace(string(out))))
				}
			}
		}

		res.output(jsonMode)
		os.Exit(res.exitCode())
		return nil
	},
}

func init() {
	planCheckCmd.Flags().Bool("json", false, "Output result as JSON")
	doingCheckCmd.Flags().Bool("json", false, "Output result as JSON")
	learningCheckCmd.Flags().Bool("json", false, "Output result as JSON")

	toolsCmd.AddCommand(genPromptCmd)
	toolsCmd.AddCommand(planCheckCmd)
	toolsCmd.AddCommand(doingCheckCmd)
	toolsCmd.AddCommand(learningCheckCmd)
	rootCmd.AddCommand(toolsCmd)
}
