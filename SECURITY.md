# Security Policy

## Intended use

These are teaching prototypes for synthetic, disposable home-lab environments.
They do not include a complete authentication, authorization, TLS, multi-user
isolation, monitoring, privacy or incident-response design. Keep endpoints
loopback-only unless you independently design and test broader exposure.
Do not submit real credentials, private logs, personal data or irreplaceable
configuration. Model requests can leave the application host if you configure
a remote provider; local application code does not imply local inference.

## Reporting a problem

Check the public repository's Security tab for a private reporting route. Its
availability has not been established by this working revision. If none is
offered, do not publish exploit details or sensitive material in an issue; ask
the maintainer to arrange a private channel without disclosing the vulnerability.

For ordinary correctness problems without sensitive content, provide a minimal
synthetic reproduction, expected and observed behavior, project, source commit,
release tag and dependency versions. Never attach real infrastructure secrets.

## Release scope

The preserved first-edition tag is `book-v1.0.0`; the revised code's edition
identity is `book-v2.0.0`. Verify the public tag and printed commit before use.
See [BOOK_VERSION.md](BOOK_VERSION.md). Neither tag promises production support,
a response-time commitment or security certification. Dependency auditing and
testing are bounded observations; see [dependencies](docs/dependencies.md).
