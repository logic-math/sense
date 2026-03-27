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

func init() {
	doingCmd.AddCommand(doingDagCmd)
	doingCmd.AddCommand(doingNextTaskCmd)
	rootCmd.AddCommand(doingCmd)
}
