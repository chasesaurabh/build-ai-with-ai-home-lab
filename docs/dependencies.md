# Dependency scope and updates

The October 30 revision pins Python 3.12.16's Linux base image by digest in each
Dockerfile. Each project has `constraints.txt` for all packages observed in its
Linux x86_64 test image, including transitive dependencies. Runtime and test
requirements share these constraints. A runtime image installs only the runtime
requirements; listing pytest in constraints does not install it there.

These are version constraints, not a cross-platform, artifact-hash lock or an
offline dependency archive. Package indexes and image registries must remain
available; another platform can select additional dependencies or fail to find
a compatible wheel. Builds use wheel-only installation and retain no downloaded
wheel archive. Do not claim full reproducibility from a tag alone.

The base image originally supplied pip 25.0.1. Docker builds now install the
pinned pip 26.2.1 wheel before application dependencies. Project 3 now shares
the tested FastAPI 0.141.1, Starlette 1.10.0, Uvicorn 0.53.0 and HTTPX2 2.13.0
family used in Projects 1 and 2. This replaces its older Starlette dependency
after an OSV package/version query returned known advisories. Historical images
and logs are evidence of earlier runs, not recommended current dependencies.

## Updating a pin

Create a new branch or checkout, review upstream release notes and advisories,
update both direct requirements and constraints where needed, build fresh
images and run the complete test and first-run script. Verify actual installed
versions with `python -m pip list` and consistency with `python -m pip check`.
Exercise the model-backed HTTP path when a web/provider dependency changes.
Preserve the original failure and the new result. Never silently move a book tag.

Known-advisory queries are time-sensitive and incomplete. A clean Python package
query does not audit Debian OS packages, container configuration, model weights,
application design or future vulnerabilities. Repeat it before deployment.

The original companion code uses MIT. Installed dependencies retain their own
licenses and notices; inspect each package's distribution metadata/license files
before redistribution. No dependency source, model weight or container image is
included in this source repository. The local build's license inventory is part
of production evidence, not a claim of legal certification.

Python was subsequently advanced from 3.12.14 to the October 25 security release 3.12.16, with a new base-image digest and all four walkthroughs rerun. Earlier Python 3.12.14 model runs remain labeled experiments; a later interpreter does not rewrite their environment. Official release: https://www.python.org/downloads/release/python-31216/
