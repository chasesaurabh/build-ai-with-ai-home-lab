# Backup Service Operations

## Healthy Verification

A completed backup job is not sufficient by itself. Treat the run as verified only when the expected job completed, the verification report contains no errors, and the recorded restore point matches the intended source and time window.

## Failed Job

For a failed backup job, record the job identifier, failure time, destination status, and the smallest relevant log excerpt. Preserve the last known good restore point while the failure is investigated.

## Restore Boundary

Never overwrite live data merely to test a restore. Use an isolated destination, verify available capacity, and require human approval before any restore that could replace existing files.
