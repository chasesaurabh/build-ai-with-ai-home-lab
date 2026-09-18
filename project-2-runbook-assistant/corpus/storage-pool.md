# Storage Pool Operations

## Degraded Redundancy

A degraded storage pool has lost redundancy even when files remain accessible. Record the pool name and affected device, avoid starting nonessential write-heavy work, and arrange human review before replacing hardware.

## Evidence to Collect

Collect the storage service status, the pool health summary, the affected device identifier, and recent storage logs. Preserve the original output; do not run repair or replacement commands merely to gather evidence.

## Recovery Boundary

This runbook does not authorize automatic disk replacement, pool repair, resilver cancellation, or data deletion. A human must verify backups, device identity, and the rollback or recovery path before approving a change.
