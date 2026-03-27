package cmd

import (
	"fmt"
	"io"
	"os"
	"path/filepath"

	"github.com/spf13/cobra"
	"github.com/sunquan/sense/internal/workspace"
)

var learningCmd = &cobra.Command{
	Use:   "learning",
	Short: "Learning phase commands",
}

var learningMergeCmd = &cobra.Command{
	Use:   "merge <job_id>",
	Short: "Merge learning artifacts into .sense/ project context",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		jobID := args[0]
		cwd, err := os.Getwd()
		if err != nil {
			return fmt.Errorf("get working directory: %w", err)
		}

		learningDir := workspace.GetJobLearningDir(cwd, jobID)
		senseDir := workspace.GetSenseDir(cwd)

		var added, updated int

		// Merge wiki/
		wikiSrc := filepath.Join(learningDir, "wiki")
		wikiDst := filepath.Join(senseDir, "wiki")
		a, u, err := mergeDir(wikiSrc, wikiDst)
		if err != nil {
			return fmt.Errorf("merge wiki: %w", err)
		}
		added += a
		updated += u

		// Merge skills/
		skillsSrc := filepath.Join(learningDir, "skills")
		skillsDst := filepath.Join(senseDir, "skills")
		a, u, err = mergeDir(skillsSrc, skillsDst)
		if err != nil {
			return fmt.Errorf("merge skills: %w", err)
		}
		added += a
		updated += u

		// Handle OKR.md and SPEC.md if present in learning root
		for _, name := range []string{"OKR.md", "SPEC.md"} {
			src := filepath.Join(learningDir, name)
			dst := filepath.Join(senseDir, name)
			if _, err := os.Stat(src); os.IsNotExist(err) {
				continue
			}
			fmt.Printf("Learning produced %s. Updating %s...\n", name, dst)
			if err := copyFile(src, dst); err != nil {
				return fmt.Errorf("update %s: %w", name, err)
			}
			updated++
		}

		fmt.Printf("Merge complete: %d added, %d updated\n", added, updated)
		return nil
	},
}

// mergeDir copies all files from src directory into dst directory.
// Returns counts of added and updated files.
func mergeDir(src, dst string) (added, updated int, err error) {
	if _, err := os.Stat(src); os.IsNotExist(err) {
		return 0, 0, nil
	}
	if err := os.MkdirAll(dst, 0755); err != nil {
		return 0, 0, fmt.Errorf("create dst dir %s: %w", dst, err)
	}

	entries, err := os.ReadDir(src)
	if err != nil {
		return 0, 0, fmt.Errorf("read src dir %s: %w", src, err)
	}

	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		srcPath := filepath.Join(src, e.Name())
		dstPath := filepath.Join(dst, e.Name())

		isNew := false
		if _, err := os.Stat(dstPath); os.IsNotExist(err) {
			isNew = true
		}

		if err := copyFile(srcPath, dstPath); err != nil {
			return added, updated, fmt.Errorf("copy %s: %w", e.Name(), err)
		}

		if isNew {
			fmt.Printf("  added:   %s\n", dstPath)
			added++
		} else {
			fmt.Printf("  updated: %s\n", dstPath)
			updated++
		}
	}
	return added, updated, nil
}

func copyFile(src, dst string) error {
	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()

	out, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer out.Close()

	if _, err := io.Copy(out, in); err != nil {
		return err
	}
	return out.Sync()
}

func init() {
	learningCmd.AddCommand(learningMergeCmd)
	rootCmd.AddCommand(learningCmd)
}
