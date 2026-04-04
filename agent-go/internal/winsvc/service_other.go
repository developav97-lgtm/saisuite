//go:build !windows

package winsvc

import "fmt"

// installWindows is a stub for non-Windows platforms.
func installWindows() error {
	return fmt.Errorf("Windows Service installation is only supported on Windows")
}

// uninstallWindows is a stub for non-Windows platforms.
func uninstallWindows() error {
	return fmt.Errorf("Windows Service uninstallation is only supported on Windows")
}
