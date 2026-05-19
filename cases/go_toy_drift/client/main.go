package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

func main() {
	paths := os.Getenv("GO_ADAPTER_PACKAGE_PATHS")
	parts := strings.Split(paths, string(os.PathListSeparator))
	if len(parts) == 0 || parts[0] == "" {
		fmt.Fprintln(os.Stderr, "GO_ADAPTER_PACKAGE_PATHS was empty")
		os.Exit(2)
	}

	value, err := os.ReadFile(filepath.Join(parts[0], "value.txt"))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	fmt.Println(strings.TrimSpace(string(value)))
}
