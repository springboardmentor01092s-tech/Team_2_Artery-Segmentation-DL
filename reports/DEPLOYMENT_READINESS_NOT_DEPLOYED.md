# Deployment readiness — not deployed — 17 November 2026

## 20 November 2026 final container-security position

Trivy 0.76.2 completed an offline scan of `corovision:automatic-report-acceptance` after downloading public advisory databases separately. The image resolved to `sha256:287415856e54bc7ac7af079ecea61cdb78c18a8b017c61f2ae9a5f62fa8a1c5b`. The JSON report contains 407 findings: **3 critical, 68 high, 155 medium, 164 low and 17 unknown**. Pillow has no finding after the Pillow 13 upgrade. The critical findings affect Debian `libglib2.0-0`, `libsqlite3-0` and `zlib1g`; the scan listed no fixed Debian version for them. Eight high findings list fixes, including Python `urllib3` 2.7.0 with 2.8.0 available. Scan execution passed; security acceptance remains **OPEN** pending dependency/base-image remediation or explicit risk acceptance and a fresh rebuild/rescan. Evidence: `container_vulnerability_rescan_20261119.json`, SHA-256 `42f32697a608fa83211f0c8e580fbabe4bcadbe78c3216c568ddc08e77d309f0`.

Deployment was intentionally not performed.

## Disposable PostgreSQL rehearsal increment — 17 November 2026

### Populated recovery follow-up

`scripts/rehearse_postgres_records.py` restricts access to localhost databases named `corovision_rehearsal_*` and refuses to seed an already populated database. Created `corovision_rehearsal_source`, seeded a disabled synthetic researcher, a CTA case and a completed synthetic volume record with null severity/abstained quality. ORM persistence/query checks passed. Backed it up with `pg_dump -Fc`, restored using `pg_restore --exit-on-error` into `corovision_rehearsal_restored`, and reran verification. Both snapshots had SHA-256 `3352aaf7252e54c74a1f76982452e932fcb40c8592f0a08d4395cd2f187b2375`. Populated ORM persistence and backup/restore: PASS. Backup: `/tmp/corovision-pg-rehearsal.GFGTxr/populated.dump`. Temporary server stopped; current application database untouched. HTTP authorization/report generation on PostgreSQL and legacy upgrade migrations remain NOT_TESTED.

Using local PostgreSQL 16 in `/tmp/corovision-pg-rehearsal.GFGTxr`, initialized a separate UTF-8 cluster, listening only on localhost port 55439. SQLAlchemy application metadata created **31 tables** successfully. `pg_dump -Fc` backed up this schema and `pg_restore --exit-on-error` restored into separate database `corovision_restore`; the restored public table count was **31**. The temporary server was stopped afterward. Existing application databases were untouched. Backup artifact: `/tmp/corovision-pg-rehearsal.GFGTxr/schema.dump` (temporary, not a durable release artifact).

Fresh-schema compatibility and schema-only recovery: PASS. Populated case/analysis/API/report rehearsal, legacy PostgreSQL upgrade migration and data rollback: NOT_TESTED. Current `upgrade_local_schema` only upgrades SQLite and explicitly returns for PostgreSQL; fresh metadata creation is not evidence of a PostgreSQL upgrade path. Docker daemon remains unavailable (missing socket), so container builds/scans remain BLOCKED_BY_ENVIRONMENT.

| Area | Current position | Required before authorization |
| --- | --- | --- |
| Containers | Local application packaging exists | Rebuild pinned production images; scan and sign |
| Database | Working local persistence | Rehearse non-destructive PostgreSQL migration and rollback |
| Inference | Integrated application workers | Separate bounded CPU/GPU queues, timeouts and health checks |
| Storage | Local protected access paths | Configure durable encrypted object storage and retention |
| Auth/RBAC | Application authorization tests pass | Production secrets, bootstrap admin rotation and session policy |
| Operations | Application logs exist | Central logs, metrics, alerting, audit retention and runbooks |
| Recovery | Evidence is versioned | Backup/restore drill with RPO/RTO and artifact reconciliation |
| Hosting | Not provisioned | Environment, DNS/TLS, capacity and security acceptance |

No Railway resource, DNS record, production database, secret, or hosted service was changed. Readiness: **PARTIAL; NOT DEPLOYED**.

## Locally executed on 17 November 2026

- Preflight: Docker 29.9.3 and Compose 5.7.0 CLIs detected; required files and disk check passed.
- `docker compose config --quiet`: PASS with an ephemeral local-only secret value.
- Backup/restore, container-contract and operations tests: 10 passed.
- `docker build --check .`: BLOCKED because the Docker Desktop daemon socket was not running.
- PostgreSQL migration rehearsal, production image build, vulnerability scan and hosted recovery remain NOT_TESTED.
