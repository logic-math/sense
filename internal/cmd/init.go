package cmd

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
	"github.com/sunquan/sense/internal/workspace"
)

var initCmd = &cobra.Command{
	Use:   "init",
	Short: "Initialize a sense workspace in the current directory",
	RunE: func(cmd *cobra.Command, args []string) error {
		cwd, err := os.Getwd()
		if err != nil {
			return fmt.Errorf("get working directory: %w", err)
		}
		if err := workspace.Init(cwd); err != nil {
			return fmt.Errorf("init workspace: %w", err)
		}
		fmt.Println("Initialized sense workspace in", cwd)
		return nil
	},
}

func init() {
	rootCmd.AddCommand(initCmd)
}
