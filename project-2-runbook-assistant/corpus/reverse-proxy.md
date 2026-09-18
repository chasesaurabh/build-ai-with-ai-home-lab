# Reverse Proxy Operations

## TLS Handshake Errors

Intermittent TLS handshake errors can originate at the listener, certificate chain, client compatibility boundary, or upstream connection. First establish whether the failure affects every client or only a subset.

## Evidence to Collect

Collect a bounded sample of recent proxy logs, the listener status, certificate validity dates, and a network reachability observation for the configured upstream. Remove tokens, cookies, authorization headers, and private keys before sharing evidence.

## Upstream Unreachable

If the proxy is healthy but the upstream is unreachable, record the affected route and time window. Do not weaken certificate validation or expose a private upstream as a diagnostic shortcut.
