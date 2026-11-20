# Clean GitHub release check — 20 November 2026

## Result: release acceptance blocked

The public `lingareddy-dhanush` branch was cloned into a new temporary
directory with no source-tree, model, database, environment, or browser state
copied from this workspace. Its exact revision was
`f2ea58743af251706bc4d509e140321cf024bb18`; `git status --porcelain` was empty.

The clone passed `scripts/configure.py`, `scripts/preflight.py`,
`docker compose config --quiet`, image build, startup, and
`/api/health/ready`. The image downloaded and hash-validated its documented
2D model release during the build. The health response reported 2D available,
3D optional checkpoint unavailable, persistent storage ready, and a configured
worker.

However, `GET /openapi.json` from the running clean-clone application showed
that `/api/admin/invitations` is absent. Therefore the published revision does
not include the local administrator MFA/invitation implementation and cannot
pass the required bootstrap-to-invitation acceptance. The disposable Compose
project and volume were removed after the check.

## Security inventory status

The retained Debian 13 offline scan contains 123 high findings and zero
critical findings. They remain **untriaged**, not accepted. The largest package
groups are `libgssapi-krb5-2`, `libk5crypto3`, `libkrb5-3`, and
`libkrb5support0` (14 findings each), followed by core utility and library
packages. Per-CVE package/fixed-version/runtime-exposure dispositions are still
required before a release decision. The scan cannot be treated as a security
pass merely because critical findings are zero.

## Required next action

Publish a reviewed revision containing the locally verified authentication and
documentation changes, then repeat this clean-clone check from that immutable
revision. Do not use the current dirty workspace as release evidence.
