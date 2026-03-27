package cmd

import (
	"fmt"
	"os"
	"strings"

	"github.com/spf13/cobra"
	"github.com/sunquan/sense/internal/executor"
	"github.com/sunquan/sense/internal/workspace"
)

var jobCmd = &cobra.Command{
	Use:   "job",
	Short: "Job management commands",
}

var jobListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all jobs and their overall status",
	Args:  cobra.NoArgs,
	RunE: func(cmd *cobra.Command, args []string) error {
		cwd, err := os.Getwd()
		if err != nil {
			return fmt.Errorf("get working directory: %w", err)
		}

		ids, err := workspace.ListJobIDs(cwd)
		if err != nil {
			return fmt.Errorf("list jobs: %w", err)
		}

		if len(ids) == 0 {
			fmt.Println("No jobs found.")
			return nil
		}

		fmt.Printf("%-12s %-10s  %s\n", "JOB_ID", "STATUS", "TASKS")
		fmt.Println(strings.Repeat("-", 50))

		for _, jobID := range ids {
			doingDir := workspace.GetJobDoingDir(cwd, jobID)
			tj, err := executor.Load(doingDir)
			if err != nil {
				fmt.Printf("%-12s %-10s  (no tasks.json)\n", jobID, "unknown")
				continue
			}
			status := inferJobStatus(tj)
			total := len(tj.Tasks)
			done := 0
			for _, t := range tj.Tasks {
				if t.Status == executor.StatusSuccess {
					done++
				}
			}
			fmt.Printf("%-12s %-10s  %d/%d done\n", jobID, status, done, total)
		}
		return nil
	},
}

// inferJobStatus derives a single job status from its tasks.
func inferJobStatus(tj *executor.TasksJSON) string {
	hasFailed := false
	hasRunning := false
	hasPending := false
	for _, t := range tj.Tasks {
		switch t.Status {
		case executor.StatusFailed:
			hasFailed = true
		case executor.StatusRunning:
			hasRunning = true
		case executor.StatusPending:
			hasPending = true
		}
	}
	if hasFailed {
		return "failed"
	}
	if hasRunning {
		return "running"
	}
	if hasPending {
		return "pending"
	}
	return "success"
}

func init() {
	jobCmd.AddCommand(jobListCmd)
	rootCmd.AddCommand(jobCmd)
}
