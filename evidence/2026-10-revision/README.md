# October 2026 revision evidence

This is the revision evidence bundle. Evidence files alone do not prove a
public tag exists. Consult `BOOK_VERSION.md` and verify your acquired release.

The seven run directories retain exact synthetic model-evaluation outputs,
including the first intake miss and first runbook conflict failure. Their
manifests select relevant fields from private production records and identify
both originals by hash. No case, answer or score has been edited. Application
source hashes and image identities describe the run that actually occurred;
do not assume they are the later dependency-refresh images.

`software-and-walkthroughs.json` extracts the actual success/test lines from
the four later first-run logs. It does not include whole build transcripts.
`dependency-inventory.json` records that later test environment and confirms
pip dependency consistency. The accompanying dated OSV query returned no
advisories for its 22 distinct Python package/version pairs. This does not
audit the OS image or prove that vulnerabilities are absent.

No human-independent semantic review is claimed. Outputs include static
fixtures, known replay sets and synthetic prompt-injection text (including
fake paths). These are test inputs, not instructions or real credentials.
The planner harness does not pull images or scale real infrastructure.
See each project's EVIDENCE.md for scope, misses and historical observations.

This bundle excludes book prose, cover/interior artwork, private production
notes, personal data, model weights and downloaded third-party packages.

The `live-intake-013` run verifies the current adapter and dependency-refresh
image on the same 12 development cases: 12/12, zero provider errors. The earlier
004/005 results remain recorded experiments, but 005 has a different adapter
hash and its old image was unavailable for a byte-level comparison. Do not
silently attribute those earlier outcomes to the final adapter. The later run
is a known-case regression check, not independent validation or a new holdout.

## Later Python security refresh

The files prefixed `python31216-` are the latest software/dependency observations:
Python3.12.16, the newly pinned base digest, all195 software tests, four complete
first-run scripts and a repeated OSV query with no returned Python advisories.
The unprefixed inventory and walkthrough files preserve the earlier3.12.14 run.
Model-evaluation output files retain the image identity actually used; they are
not relabeled as experiments on the later interpreter. These remain different
checks with different scope.

## CPU-only endpoint starter

`model-bootstrap-010` and `011` preserve two runs that downloaded the Qwen 4B
model into empty Docker volumes; `012` tests the final script with retained
services, an additional manual HTTP request and scoped cleanup. The latter
reuses downloaded model files. Each tests one synthetic intake case before
and after stopping/restarting Ollama 0.40.12, including controlled failure while
the provider is down. This is compatibility and lifecycle evidence, not model
accuracy or evidence for Projects 2–4. Resource snapshots are not peak or
minimum-machine measurements. See [the complete starter guide](../../docs/local-model-starter.md).
