package executor

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

const tasksJSONVersion = "1.0"

// TaskStatus represents the execution status of a task.
type TaskStatus string

const (
	StatusPending TaskStatus = "pending"
	StatusRunning TaskStatus = "running"
	StatusSuccess TaskStatus = "success"
	StatusFailed  TaskStatus = "failed"
)

// TaskRecord is a single task entry in tasks.json.
type TaskRecord struct {
	TaskID       string     `json:"task_id"`
	TaskName     string     `json:"task_name"`
	TaskFile     string     `json:"task_file,omitempty"`
	Status       TaskStatus `json:"status"`
	Dependencies []string   `json:"dependencies"`
	Attempts     int        `json:"attempts"`
	CommitHash   string     `json:"commit_hash,omitempty"`
	CreatedAt    time.Time  `json:"created_at"`
	UpdatedAt    time.Time  `json:"updated_at"`
}

// TasksJSON is the root structure of tasks.json.
type TasksJSON struct {
	Version   string       `json:"version"`
	CreatedAt time.Time    `json:"created_at"`
	UpdatedAt time.Time    `json:"updated_at"`
	Tasks     []TaskRecord `json:"tasks"`
}

// Load reads tasks.json from the given doing directory.
func Load(doingDir string) (*TasksJSON, error) {
	path := filepath.Join(doingDir, "tasks.json")
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read tasks.json: %w", err)
	}
	var tj TasksJSON
	if err := json.Unmarshal(data, &tj); err != nil {
		return nil, fmt.Errorf("parse tasks.json: %w", err)
	}
	return &tj, nil
}

// Save writes tasks.json to the given doing directory atomically.
func Save(doingDir string, tj *TasksJSON) error {
	tj.UpdatedAt = time.Now()
	path := filepath.Join(doingDir, "tasks.json")
	data, err := json.MarshalIndent(tj, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal tasks.json: %w", err)
	}
	tmp := path + ".tmp"
	if err := os.WriteFile(tmp, data, 0644); err != nil {
		return fmt.Errorf("write tasks.json tmp: %w", err)
	}
	if err := os.Rename(tmp, path); err != nil {
		return fmt.Errorf("rename tasks.json: %w", err)
	}
	return nil
}

// NewTasksJSON creates a TasksJSON from a topologically sorted DAG.
func NewTasksJSON(dag *DAG, order []string) *TasksJSON {
	now := time.Now()
	tj := &TasksJSON{
		Version:   tasksJSONVersion,
		CreatedAt: now,
		UpdatedAt: now,
	}

	// Build node map for quick lookup.
	nodeMap := make(map[string]*Node, len(dag.Nodes))
	for _, n := range dag.Nodes {
		nodeMap[n.TaskID] = n
	}

	for _, id := range order {
		n := nodeMap[id]
		var deps []string
		if len(n.Deps) > 0 {
			deps = n.Deps
		}
		tj.Tasks = append(tj.Tasks, TaskRecord{
			TaskID:       n.TaskID,
			TaskName:     n.TaskName,
			TaskFile:     n.TaskFile,
			Status:       StatusPending,
			Dependencies: deps,
			Attempts:     0,
			CreatedAt:    now,
			UpdatedAt:    now,
		})
	}
	return tj
}

// UpdateStatus sets the status of a task and updates timestamps.
func (tj *TasksJSON) UpdateStatus(taskID string, status TaskStatus) error {
	for i := range tj.Tasks {
		if tj.Tasks[i].TaskID == taskID {
			tj.Tasks[i].Status = status
			tj.Tasks[i].UpdatedAt = time.Now()
			tj.UpdatedAt = time.Now()
			return nil
		}
	}
	return fmt.Errorf("task %q not found", taskID)
}

// UpdateAttempts sets the attempts count of a task.
func (tj *TasksJSON) UpdateAttempts(taskID string, attempts int) error {
	for i := range tj.Tasks {
		if tj.Tasks[i].TaskID == taskID {
			tj.Tasks[i].Attempts = attempts
			tj.Tasks[i].UpdatedAt = time.Now()
			tj.UpdatedAt = time.Now()
			return nil
		}
	}
	return fmt.Errorf("task %q not found", taskID)
}

// UpdateCommit sets the commit hash of a task.
func (tj *TasksJSON) UpdateCommit(taskID, commitHash string) error {
	for i := range tj.Tasks {
		if tj.Tasks[i].TaskID == taskID {
			tj.Tasks[i].CommitHash = commitHash
			tj.Tasks[i].UpdatedAt = time.Now()
			tj.UpdatedAt = time.Now()
			return nil
		}
	}
	return fmt.Errorf("task %q not found", taskID)
}

// NextTask returns the task_id of the first pending task whose all dependencies
// have status "success". Returns "" if no such task exists.
func (tj *TasksJSON) NextTask() string {
	// Build a status map for quick lookup.
	statusMap := make(map[string]TaskStatus, len(tj.Tasks))
	for _, t := range tj.Tasks {
		statusMap[t.TaskID] = t.Status
	}

	for _, t := range tj.Tasks {
		if t.Status != StatusPending {
			continue
		}
		allDone := true
		for _, dep := range t.Dependencies {
			if statusMap[dep] != StatusSuccess {
				allDone = false
				break
			}
		}
		if allDone {
			return t.TaskID
		}
	}
	return ""
}
