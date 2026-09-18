# Troubleshooting

## Tests fail during image build

Confirm the project directory contains its `app`, `tests`, fixtures, and eval case files. Rebuild from a clean checkout of the edition tag. A cached image is not proof that a clean environment can still resolve every dependency.

## The application is live but not ready

Liveness means the process runs. Readiness means required dependencies can serve the intended request. Check the configured model base URL, served model alias, timeout, and provider response before changing application policy.

## HTTP 502 from a model-backed request

Inspect the controlled error category and a sanitized provider response. Common causes include a malformed envelope, invalid JSON, provider-compatible output that fails the stricter application schema, or a policy postcondition failure. Do not coerce invalid values silently.

## An eval produces empty or truncated content

Check the provider's reasoning mode, output limit, structured-output implementation, and finish reason. Preserve the raw failure. A larger token limit can expose a loop rather than solve the contract mismatch.

## Retrieval returns no evidence

Run the retrieval-only eval before changing generation. Verify corpus manifests, parsing, stable passage IDs, the expected passage rank, and the abstention threshold.

## A tool or plan is rejected

Inspect the requested service, tool name, arguments, duplicate calls, budget, and evidence IDs. Rejection is the correct result for an unknown tool, cross-target request, arbitrary path, extra field, or exceeded budget.

## A candidate will not start

Treat the package, schema, and environment as separate layers. Inspect the container error, validate the complete candidate, and restore the recorded baseline. Do not weaken validation merely to make the candidate start.

