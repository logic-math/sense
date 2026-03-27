package workspace

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

const senseDirName = ".sense"

// Init creates the .sense/ directory structure in the given root directory.
func Init(root string) error {
	senseDir := filepath.Join(root, senseDirName)

	dirs := []string{
		senseDir,
		filepath.Join(senseDir, "wiki"),
		filepath.Join(senseDir, "skills"),
		filepath.Join(senseDir, "jobs"),
	}
	for _, d := range dirs {
		if err := os.MkdirAll(d, 0755); err != nil {
			return fmt.Errorf("create dir %s: %w", d, err)
		}
	}

	files := map[string]string{
		filepath.Join(senseDir, "OKR.md"):  "# OKR\n",
		filepath.Join(senseDir, "SPEC.md"): "# SPEC\n",
	}
	for path, content := range files {
		if _, err := os.Stat(path); os.IsNotExist(err) {
			if err := os.WriteFile(path, []byte(content), 0644); err != nil {
				return fmt.Errorf("create file %s: %w", path, err)
			}
		}
	}
	return nil
}

// GetSenseDir returns the .sense/ directory path for the given root.
func GetSenseDir(root string) string {
	return filepath.Join(root, senseDirName)
}

// NextJobID returns the next job ID (e.g. "job_1", "job_2") based on existing
// job directories under <root>/jobs/. root should be the .sense/ directory.
func NextJobID(root string) (string, error) {
	jobsDir := filepath.Join(root, "jobs")
	entries, err := os.ReadDir(jobsDir)
	if err != nil {
		if os.IsNotExist(err) {
			return "job_1", nil
		}
		return "", fmt.Errorf("read jobs dir: %w", err)
	}

	max := 0
	for _, e := range entries {
		if !e.IsDir() {
			continue
		}
		name := e.Name()
		if !strings.HasPrefix(name, "job_") {
			continue
		}
		n, err := strconv.Atoi(strings.TrimPrefix(name, "job_"))
		if err != nil {
			continue
		}
		if n > max {
			max = n
		}
	}
	return fmt.Sprintf("job_%d", max+1), nil
}

// GetJobPlanDir returns the plan directory path for a given job.
func GetJobPlanDir(root, jobID string) string {
	return filepath.Join(root, senseDirName, "jobs", jobID, "plan")
}

// GetJobDoingDir returns the doing directory path for a given job.
func GetJobDoingDir(root, jobID string) string {
	return filepath.Join(root, senseDirName, "jobs", jobID, "doing")
}

// GetJobLearningDir returns the learning directory path for a given job.
func GetJobLearningDir(root, jobID string) string {
	return filepath.Join(root, senseDirName, "jobs", jobID, "learning")
}

// ListJobIDs returns sorted job IDs under <root>/.sense/jobs/.
func ListJobIDs(root string) ([]string, error) {
	jobsDir := filepath.Join(root, senseDirName, "jobs")
	entries, err := os.ReadDir(jobsDir)
	if err != nil {
		return nil, fmt.Errorf("read jobs dir: %w", err)
	}

	var ids []string
	for _, e := range entries {
		if e.IsDir() && strings.HasPrefix(e.Name(), "job_") {
			ids = append(ids, e.Name())
		}
	}
	sort.Strings(ids)
	return ids, nil
}
