# Phase 4 — Security checklist and remediation

Functional checks passed in the full suite: authentication/session revocation,
role and case-resource authorization, ownership-scoped artifacts/reports,
upload format/geometry/size validation, invalid/missing-file paths, audit events,
error redaction, production secret validation and disabled production demo flags.
Operational logs use route templates and generated request IDs, not bodies,
tokens or patient filenames. API responses include no-store and basic security
headers. This is not a comprehensive pentest or supply-chain vulnerability scan.

Remediation this increment:

- Added offline SQLite/storage snapshot and restore utility. Explicit writer-stop
  confirmation, read-only SQLite backup source, SQLite integrity check, file size/
  SHA256 manifest, no symlink following, destination containment checks and no
  overwriting existing backup/restore targets.
- Four isolated synthetic tests passed: round-trip DB/artifact equality,
  offline/nested-output rejection, tamper rejection and symlink rejection.
- Lengthened test-only JWT fixture; no production key changed or disclosed.

Backup procedure: stop all writers; run `scripts/backup_local.py create` with
explicit database/storage/output paths and `--offline-confirmed`; protect the
destination. Restore into a new private directory with the restore subcommand,
validate it, and arrange an explicit cutover separately. Never point restore at
the running application. Secrets, checkpoint bundles and PostgreSQL are outside
this snapshot's scope. Database/storage consistency assumes the operator actually
stopped writers; the flag cannot independently prove that. Backup manifests are
checksums, not cryptographic signatures or encryption.

Remaining: actual development/production restore drill, encrypted backups/key
escrow, retention/access policy, PostgreSQL backup if used, TLS/reverse-proxy and
network isolation validation, independent security review, dependency/CVE audit
and incident-response process. No real user database/upload backup was created.
