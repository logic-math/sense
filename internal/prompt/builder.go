package prompt

import (
	"embed"
	"fmt"
	"strings"
)

//go:embed templates/*.md
var templateFS embed.FS

// Build renders a template by replacing {{variable}} placeholders with values.
func Build(templateName string, vars map[string]string) (string, error) {
	path := "templates/" + templateName + ".md"
	data, err := templateFS.ReadFile(path)
	if err != nil {
		return "", fmt.Errorf("read template %s: %w", path, err)
	}

	result := string(data)
	for k, v := range vars {
		result = strings.ReplaceAll(result, "{{"+k+"}}", v)
	}
	return result, nil
}

// TemplateNames returns the list of available template names.
func TemplateNames() []string {
	return []string{"plan", "doing", "test", "review", "learning"}
}
