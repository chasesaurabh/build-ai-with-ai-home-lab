# Container Registry Operations

## Digest Mismatch

A manifest digest mismatch means the retrieved content does not match the requested immutable digest. Stop the affected pull or promotion workflow, preserve the digest values, and investigate provenance before trusting the artifact.

## Evidence to Collect

Record the repository name, requested digest, observed digest, client time, registry status, and the smallest relevant log excerpt. Remove authorization headers and access tokens from captured evidence.

## Deletion Boundary

Do not delete tags, manifests, or blobs as a troubleshooting shortcut. Registry deletion requires a separately approved retention or incident process with a recovery plan.
