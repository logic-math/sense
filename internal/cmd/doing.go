package cmd

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/spf13/cobra"
	"github.com/sunquan/sense/internal/executor"
	"github.com/sunquan/sense/internal/parser"
	"github.com/sunquan/sense/internal/workspace"
)

var (
	updateTaskCommit   string
	updateTaskAttempts int
)

var doingCmd = &cobra.Command{
	Use:   "doing",
	Short: "Doing phase commands",
}

var doingDagCmd = &cobra.Command{
	Use:   "dag <job_id>",
	Short: "Parse plan/*.md and generate tasks.json in the doing directory",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		jobID := args[0]
		cwd, err := os.Getwd()
		if err != nil {
			return fmt.Errorf("get working directory: %w", err)
		}

		planDir := workspace.GetJobPlanDir(cwd, jobID)
		doingDir := workspace.GetJobDoingDir(cwd, jobID)

		entries, err := os.ReadDir(planDir)
		if err != nil {
			return fmt.Errorf("read plan dir %s: %w", planDir, err)
		}

		var taskEntries []executor.TaskEntry
		for _, e := range entries {
			if e.IsDir() || !strings.HasSuffix(e.Name(), ".md") {
				continue
			}
			taskID := strings.TrimSuffix(e.Name(), ".md")
			path := filepath.Join(planDir, e.Name())
			t, err := parser.ParseTaskFile(path)
			if err != nil {
				return fmt.Errorf("parse %s: %w", e.Name(), err)
			}
			taskEntries = append(taskEntries, executor.TaskEntry{
				TaskID:   taskID,
				TaskFile: e.Name(),
				Task:     t,
			})
		}

		// Sort by task ID for deterministic output.
		sort.Slice(taskEntries, func(i, j int) bool {
			return taskEntries[i].TaskID < taskEntries[j].TaskID
		})

		dag, err := executor.BuildDAG(taskEntries)
		if err != nil {
			return fmt.Errorf("build DAG: %w", err)
		}

		order, err := executor.TopologicalSort(dag)
		if err != nil {
			return fmt.Errorf("topological sort: %w", err)
		}

		tj := executor.NewTasksJSON(dag, order)

		if err := os.MkdirAll(doingDir, 0755); err != nil {
			return fmt.Errorf("create doing dir: %w", err)
		}

		if err := executor.Save(doingDir, tj); err != nil {
			return fmt.Errorf("save tasks.json: %w", err)
		}

		fmt.Printf("Generated tasks.json with %d tasks in %s\n", len(tj.Tasks), doingDir)
		return nil
	},
}

var doingNextTaskCmd = &cobra.Command{
	Use:   "next_task <job_id>",
	Short: "Return the next executable task ID from tasks.json, or NONE",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		jobID := args[0]
		cwd, err := os.Getwd()
		if err != nil {
			return fmt.Errorf("get working directory: %w", err)
		}

		doingDir := workspace.GetJobDoingDir(cwd, jobID)
		tj, err := executor.Load(doingDir)
		if err != nil {
			return fmt.Errorf("load tasks.json: %w", err)
		}

		next := tj.NextTask()
		if next == "" {
			fmt.Println("NONE")
		} else {
			fmt.Println(next)
		}
		return nil
	},
}

var doingUpdateTaskCmd = &cobra.Command{
	Use:   "update_task <job_id> <task_id> <status>",
	Short: "Update the status (and optionally commit hash / attempts) of a task in tasks.json",
	Args:  cobra.ExactArgs(3),
	RunE: func(cmd *cobra.Command, args []string) error {
		jobID, taskID, statusStr := args[0], args[1], args[2]
		status := executor.TaskStatus(statusStr)
		switch status {
		case executor.StatusPending, executor.StatusRunning, executor.StatusSuccess, executor.StatusFailed:
		default:
			return fmt.Errorf("invalid status %q: must be pending|running|success|failed", statusStr)
		}

		cwd, err := os.Getwd()
		if err != nil {
			return fmt.Errorf("get working directory: %w", err)
		}

		doingDir := workspace.GetJobDoingDir(cwd, jobID)
		tj, err := executor.Load(doingDir)
		if err != nil {
			return fmt.Errorf("load tasks.json: %w", err)
		}

		if err := tj.UpdateStatus(taskID, status); err != nil {
			return err
		}
		if updateTaskCommit != "" {
			if err := tj.UpdateCommit(taskID, updateTaskCommit); err != nil {
				return err
			}
		}
		if cmd.Flags().Changed("attempts") {
			if err := tj.UpdateAttempts(taskID, updateTaskAttempts); err != nil {
				return err
			}
		}

		if err := executor.Save(doingDir, tj); err != nil {
			return fmt.Errorf("save tasks.json: %w", err)
		}

		fmt.Printf("Updated %s/%s status=%s\n", jobID, taskID, status)
		return nil
	},
}

var doingListCmd = &cobra.Command{
	Use:   "list <job_id>",
	Short: "List all tasks in tasks.json as a table",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		jobID := args[0]
		cwd, err := os.Getwd()
		if err != nil {
			return fmt.Errorf("get working directory: %w", err)
		}

		doingDir := workspace.GetJobDoingDir(cwd, jobID)
		tj, err := executor.Load(doingDir)
		if err != nil {
			return fmt.Errorf("load tasks.json: %w", err)
		}

		fmt.Printf("%-12s %-10s %-4s  %s\n", "TASK_ID", "STATUS", "ATTS", "NAME")
		fmt.Println(strings.Repeat("-", 70))
		for _, t := range tj.Tasks {
			fmt.Printf("%-12s %-10s %-4d  %s\n", t.TaskID, string(t.Status), t.Attempts, t.TaskName)
		}
		return nil
	},
}

func init() {
	doingCmd.AddCommand(doingDagCmd)
	doingCmd.AddCommand(doingNextTaskCmd)
	doingUpdateTaskCmd.Flags().StringVar(&updateTaskCommit, "commit", "", "Commit hash to record")
	doingUpdateTaskCmd.Flags().IntVar(&updateTaskAttempts, "attempts", 0, "Attempts count to set")
	doingCmd.AddCommand(doingUpdateTaskCmd)
	doingCmd.AddCommand(doingListCmd)
	rootCmd.AddCommand(doingCmd)
}
