package cmd

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/spf13/cobra"
	"github.com/sunquan/sense/internal/parser"
	"github.com/sunquan/sense/internal/prompt"
	"github.com/sunquan/sense/internal/workspace"
)

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

		content, err := prompt.Build(phase, vars)
		if err != nil {
			return fmt.Errorf("build prompt: %w", err)
		}

		// Write to prompts/ directory
		promptsDir := filepath.Join(cwd, "prompts")
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

func init() {
	toolsCmd.AddCommand(genPromptCmd)
	rootCmd.AddCommand(toolsCmd)
}
