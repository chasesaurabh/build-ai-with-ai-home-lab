# Contributing

This repository is being prepared for its first book-aligned release. Before the public release, proposed changes should remain in local review.

When contribution opens:

1. Start from a current issue or describe the bounded outcome.
2. Use synthetic fixtures only.
3. Preserve application-owned authorization and policy.
4. Add a deterministic regression test for every correction.
5. Record behavioral changes against development cases; do not tune against the published holdout and call it fresh evidence.
6. Update the specification, threat model, and evidence summary when a boundary changes.
7. Do not add model weights, credentials, private logs, machine-specific paths, raw provider dumps, generated caches, or book-production assets.

Pull requests should state the user-visible effect, changed boundary, tests run, known limitations, and rollback or removal procedure.

