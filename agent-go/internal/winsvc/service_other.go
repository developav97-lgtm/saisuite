//go:build !windows

package winsvc

import (
	"context"
	"fmt"
)

// installWindows is a stub for non-Windows platforms.
func installWindows() error {
	return fmt.Errorf("Windows Service installation is only supported on Windows")
}

// uninstallWindows is a stub for non-Windows platforms.
func uninstallWindows() error {
	return fmt.Errorf("Windows Service uninstallation is only supported on Windows")
}

// runAsService on non-Windows just calls fn() directly (no SCM handshake needed).
func runAsService(name string, fn func(ctx context.Context)) error {
	fn(context.Background())
	return nil
}
