package prompt

import (
	"os"
	"path/filepath"
	"strings"
)

// Context holds the project context loaded from .sense/ directory.
type Context struct {
	OKR    string
	SPEC   string
	Wiki   map[string]string // filename -> content
	Skills map[string]string // filename -> content
}

// LoadContext reads OKR.md, SPEC.md, wiki/, and skills/ from the .sense/ directory.
func LoadContext(senseDir string) (*Context, error) {
	ctx := &Context{
		Wiki:   make(map[string]string),
		Skills: make(map[string]string),
	}

	okrPath := filepath.Join(senseDir, "OKR.md")
	if data, err := os.ReadFile(okrPath); err == nil {
		ctx.OKR = string(data)
	}

	specPath := filepath.Join(senseDir, "SPEC.md")
	if data, err := os.ReadFile(specPath); err == nil {
		ctx.SPEC = string(data)
	}

	ctx.Wiki = loadDir(filepath.Join(senseDir, "wiki"))
	ctx.Skills = loadDir(filepath.Join(senseDir, "skills"))

	return ctx, nil
}

func loadDir(dir string) map[string]string {
	result := make(map[string]string)
	entries, err := os.ReadDir(dir)
	if err != nil {
		return result
	}
	for _, e := range entries {
		if e.IsDir() || !strings.HasSuffix(e.Name(), ".md") {
			continue
		}
		path := filepath.Join(dir, e.Name())
		if data, err := os.ReadFile(path); err == nil {
			result[e.Name()] = string(data)
		}
	}
	return result
}

// WikiContent returns all wiki content concatenated.
func (c *Context) WikiContent() string {
	var sb strings.Builder
	for name, content := range c.Wiki {
		sb.WriteString("## " + name + "\n\n")
		sb.WriteString(content)
		sb.WriteString("\n")
	}
	return sb.String()
}

// SkillsContent returns all skills content concatenated.
func (c *Context) SkillsContent() string {
	var sb strings.Builder
	for name, content := range c.Skills {
		sb.WriteString("## " + name + "\n\n")
		sb.WriteString(content)
		sb.WriteString("\n")
	}
	return sb.String()
}
