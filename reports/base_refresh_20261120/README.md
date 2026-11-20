# Debian base refresh acceptance

The isolated candidate was built from the application checkout with the same frontend stage and released 2D model archive. Its runtime uses Debian Trixie, the corresponding GLib package, pip 26.3 and setuptools 84.2.1. The production Dockerfile remains the baseline.

| Image | Offline high findings | Offline critical findings |
| --- | ---: | ---: |
| Debian 12 baseline | 68 | 3 |
| Debian 12 with Python refresh | 61 | 3 |
| Debian 13 candidate | 123 | 0 |

Counts are scanner package findings. In the candidate, 122 high findings were in Debian and one was in pip's vendored setuptools metadata. The Debian total represents 37 unique advisory IDs. The offline database lists one Debian high finding with a fixed package version, for zlib1g. The candidate removes the baseline's critical findings from the scan and increases the count of high findings. This comparison keeps security acceptance open.

- Build recipe and log are in this directory. Image index SHA-256 is `959d30df05d68560fc7a4ee4b45b46d44791bb55f292453b430efa3f58a2255f`.
- Scanner command used `trivy image --image-src docker --offline-scan --skip-db-update --skip-java-db-update --skip-version-check --disable-telemetry --scanners vuln --severity HIGH,CRITICAL --format json`. Raw findings are in `vulnerabilities.json`.
- Runtime probe reuses `../concurrent_capacity_20261120/probe.py`. It submits two synthetic jobs and verifies owner and outsider access to exact-run report exports.

The capped probe completed at 182.7 and 377.4 seconds for the two submissions. Each report passed owner PDF, CSV and JSON export plus outsider denial. Docker reported no OOM kill. PostgreSQL API/export and backup/restore evidence is in `postgres-report-restore.log`.
