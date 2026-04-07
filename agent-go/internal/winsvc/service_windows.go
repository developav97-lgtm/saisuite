//go:build windows

package winsvc

import (
	"context"
	"fmt"
	"time"

	"golang.org/x/sys/windows/svc"
	"golang.org/x/sys/windows/svc/mgr"
)

// agentService implements svc.Handler so Windows SCM can manage the lifecycle.
type agentService struct {
	fn func(ctx context.Context)
}

// Execute is called by the Windows SCM when the service starts.
// It reports Running immediately (so SCM doesn't time out), then calls fn(ctx).
// When SCM sends Stop/Shutdown, ctx is cancelled and workers shut down gracefully.
func (s *agentService) Execute(args []string, r <-chan svc.ChangeRequest, changes chan<- svc.Status) (bool, uint32) {
	const cmdsAccepted = svc.AcceptStop | svc.AcceptShutdown

	changes <- svc.Status{State: svc.StartPending}
	changes <- svc.Status{State: svc.Running, Accepts: cmdsAccepted}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	done := make(chan struct{})
	go func() {
		defer close(done)
		s.fn(ctx)
	}()

	for {
		select {
		case c := <-r:
			switch c.Cmd {
			case svc.Stop, svc.Shutdown:
				cancel()
				changes <- svc.Status{State: svc.StopPending}
				<-done
				return false, 0
			}
		case <-done:
			return false, 0
		}
	}
}

// runAsService registers fn with the Windows SCM under the given service name.
// fn receives a context that is cancelled when SCM sends Stop/Shutdown.
func runAsService(name string, fn func(ctx context.Context)) error {
	return svc.Run(name, &agentService{fn: fn})
}

// installWindows registers the agent as a Windows Service using the Windows Service Manager.
func installWindows() error {
	exePath, err := executablePath()
	if err != nil {
		return err
	}

	m, err := mgr.Connect()
	if err != nil {
		return fmt.Errorf("failed to connect to service manager: %w", err)
	}
	defer m.Disconnect()

	// Check if service already exists
	s, err := m.OpenService(serviceName)
	if err == nil {
		s.Close()
		return fmt.Errorf("service '%s' already exists; uninstall first", serviceName)
	}

	s, err = m.CreateService(serviceName, exePath, mgr.Config{
		DisplayName: serviceDisplayName,
		Description: serviceDescription,
		StartType:   mgr.StartAutomatic,
	}, "serve")
	if err != nil {
		return fmt.Errorf("failed to create service: %w", err)
	}
	defer s.Close()

	// Set recovery action: restart the service after 60 seconds on failure
	err = s.SetRecoveryActions([]mgr.RecoveryAction{
		{Type: mgr.ServiceRestart, Delay: 60 * time.Second},
		{Type: mgr.ServiceRestart, Delay: 60 * time.Second},
		{Type: mgr.ServiceRestart, Delay: 60 * time.Second},
	}, 86400) // Reset failure count after 24 hours
	if err != nil {
		// Non-fatal: service is installed but without recovery actions
		fmt.Printf("Warning: could not set recovery actions: %v\n", err)
	}

	return nil
}

// uninstallWindows removes the agent Windows Service.
func uninstallWindows() error {
	m, err := mgr.Connect()
	if err != nil {
		return fmt.Errorf("failed to connect to service manager: %w", err)
	}
	defer m.Disconnect()

	s, err := m.OpenService(serviceName)
	if err != nil {
		return fmt.Errorf("service '%s' not found: %w", serviceName, err)
	}
	defer s.Close()

	// Stop the service first if running
	status, err := s.Query()
	if err == nil && status.State == svc.Running {
		_, err = s.Control(svc.Stop)
		if err != nil {
			fmt.Printf("Warning: could not stop service: %v\n", err)
		}
	}

	err = s.Delete()
	if err != nil {
		return fmt.Errorf("failed to delete service: %w", err)
	}

	return nil
}
