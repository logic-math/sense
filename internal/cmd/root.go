package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
)

var version = "0.1.0"

var rootCmd = &cobra.Command{
	Use:     "sense",
	Short:   "Context-First AI Coding Framework",
	Version: version,
}

func Execute() error {
	return rootCmd.Execute()
}

func init() {
	rootCmd.SetVersionTemplate(fmt.Sprintf("sense version %s\n", version))
}
