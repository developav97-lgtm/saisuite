// Package winsvc provides Windows Service installation and management.
// It uses golang.org/x/sys/windows/svc for service lifecycle management.
// On non-Windows platforms, all functions return an error indicating
// the platform is not supported.
package winsvc

import (
	"fmt"
	"os"
	"path/filepath"
	"runtime"
)

const (
	serviceName        = "SaicloudAgent"
	serviceDisplayName = "Saicloud Agent"
	serviceDescription = "Syncs Saiopen (Firebird) data to Saicloud (Django/PostgreSQL)"
)

// Install registers the Saicloud Agent as a Windows Service.
// The service is configured to start automatically with the "serve" argument.
func Install() error {
	if runtime.GOOS != "windows" {
		return fmt.Errorf("Windows Service management is only available on Windows (current OS: %s)", runtime.GOOS)
	}
	return installWindows()
}

// Uninstall removes the Saicloud Agent Windows Service.
func Uninstall() error {
	if runtime.GOOS != "windows" {
		return fmt.Errorf("Windows Service management is only available on Windows (current OS: %s)", runtime.GOOS)
	}
	return uninstallWindows()
}

// executablePath returns the full path to the current executable.
func executablePath() (string, error) {
	exe, err := os.Executable()
	if err != nil {
		return "", fmt.Errorf("cannot determine executable path: %w", err)
	}
	return filepath.Abs(exe)
}
