package executor

import "fmt"

// TopologicalSort performs Kahn's algorithm on the DAG and returns task IDs
// in topological order. Returns an error if a cycle is detected.
func TopologicalSort(dag *DAG) ([]string, error) {
	// Build in-degree map and adjacency list.
	inDegree := make(map[string]int, len(dag.Nodes))
	adj := make(map[string][]string, len(dag.Nodes))

	for _, node := range dag.Nodes {
		if _, ok := inDegree[node.TaskID]; !ok {
			inDegree[node.TaskID] = 0
		}
		for _, dep := range node.Deps {
			adj[dep] = append(adj[dep], node.TaskID)
			inDegree[node.TaskID]++
		}
	}

	// Enqueue all nodes with in-degree 0.
	var queue []string
	for _, node := range dag.Nodes {
		if inDegree[node.TaskID] == 0 {
			queue = append(queue, node.TaskID)
		}
	}

	var order []string
	for len(queue) > 0 {
		cur := queue[0]
		queue = queue[1:]
		order = append(order, cur)

		for _, next := range adj[cur] {
			inDegree[next]--
			if inDegree[next] == 0 {
				queue = append(queue, next)
			}
		}
	}

	if len(order) != len(dag.Nodes) {
		return nil, fmt.Errorf("cycle detected in task dependencies")
	}

	return order, nil
}
