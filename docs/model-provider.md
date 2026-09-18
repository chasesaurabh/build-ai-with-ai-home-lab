# Model Provider Configuration

The projects use a narrow application-facing adapter rather than embedding model-server administration into application code.

Default examples expect:

- base URL: `http://127.0.0.1:8100` when an eval runs on the host;
- container URL: `http://host.docker.internal:8100` in the supplied Compose files;
- served model alias: `nemotron-35-lightning`;
- OpenAI-compatible chat-completions behavior;
- provider-side structured output where the project uses a schema;
- deterministic application validation after every provider response.

Use command-line options or environment variables to select another approved endpoint. Do not edit business policy merely to accommodate provider output.

## Compatibility rule

A successful network response is not enough. For each candidate provider or model, verify:

1. requested model identity resolves as intended;
2. structured-output requests are accepted;
3. returned content parses and passes the complete application schema;
4. timeouts and malformed responses map to controlled application errors;
5. the model cannot introduce extra fields, tools, targets, or authority;
6. the same frozen cases and scorer are used for comparison.

Record the model root, served alias, server version, decoding settings, date, cases, raw results, and limitations. Friendly aliases are not immutable evidence identities.

