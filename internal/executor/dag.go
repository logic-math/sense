package executor

import (
	"fmt"

	"github.com/sunquan/sense/internal/parser"
)

// Node represents a task node in the DAG.
type Node struct {
	TaskID   string
	TaskName string
	TaskFile string
	Deps     []string
}

// DAG holds the directed acyclic graph of tasks.
type DAG struct {
	Nodes []*Node
	// nodeByID maps task_id to Node for quick lookup.
	nodeByID map[string]*Node
}

// BuildDAG constructs a DAG from a list of (taskID, taskFile, task) tuples.
// It validates that all declared dependencies exist and that there are no cycles.
func BuildDAG(tasks []TaskEntry) (*DAG, error) {
	dag := &DAG{
		nodeByID: make(map[string]*Node),
	}

	for _, te := range tasks {
		node := &Node{
			TaskID:   te.TaskID,
			TaskName: te.Task.Name,
			TaskFile: te.TaskFile,
			Deps:     te.Task.Dependencies,
		}
		dag.Nodes = append(dag.Nodes, node)
		dag.nodeByID[te.TaskID] = node
	}

	// Validate all dependencies exist.
	for _, node := range dag.Nodes {
		for _, dep := range node.Deps {
			if _, ok := dag.nodeByID[dep]; !ok {
				return nil, fmt.Errorf("task %q depends on unknown task %q", node.TaskID, dep)
			}
		}
	}

	// Detect cycles via topological sort.
	if _, err := TopologicalSort(dag); err != nil {
		return nil, err
	}

	return dag, nil
}

// TaskEntry bundles a task ID, its filename, and the parsed Task.
type TaskEntry struct {
	TaskID   string
	TaskFile string
	Task     *parser.Task
}
