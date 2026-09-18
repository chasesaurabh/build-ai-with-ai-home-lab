# Certificate Authority Operations

## Expiring Certificate

For an expiring service certificate, record the subject, issuer, serial number, expiration time, intended service, and renewal owner. Confirm the replacement and rollback plan before the current certificate expires.

## Renewal Validation

Validate the renewed certificate chain, subject names, key usage, validity window, and service binding in a controlled path before deployment. Preserve the previous certificate for rollback when policy permits.

## Private Key Boundary

Never place private keys, passphrases, recovery material, or enrollment secrets in a runbook question, model prompt, log excerpt, or screenshot. A certificate can be inspected without exposing its private key.
