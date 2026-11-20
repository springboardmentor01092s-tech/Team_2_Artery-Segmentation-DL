# Defensive security audit

Disposable standard Docker, port 8003. Checks were passive or source-based. Offensive probes and generated exploit/reproduction workflows were outside this pass.

| ID | Severity / category | Evidence and observed difference | Remediation and regression |
|---|---|---|---|
| S1 | Medium / lockout | `main.py:520–550` uses account throttle; recovery now references it at `cli.py:80`. Unauthenticated abuse and recovery behavior were not reprobed. | Review combined abuse controls and verify legitimate administrator recovery |
| S2 | Not rated / enumeration | Account-specific outcomes require further review | Review uniform public responses and bounded timing tests |
| S3 | Not rated / password policy | Cross-path policy consistency unverified | Add shared policy and compare authorized inputs across paths |
| S4 | Low / production policy | 8003 GET `/docs`, `/redoc`, `/openapi.json` returned 200 without a session | Decide whether docs are public by design; if private, add production route visibility test |
| S5 | Medium / hardening gap | 8003 root response lacks CSP and HSTS; frame and content type headers present. HSTS requires verification at an HTTPS edge. | Add a compatible CSP and check effective headers on authorized HTTPS |
| S6 | Not rated / error disclosure | Not verified | Check user-facing role errors against policy |
| S7 | Not rated / session storage | `demoSessions.ts:33` removes old localStorage roster key. Current non-loopback browser path not tested. | Verify role switching is confined to dedicated demo |
| S8 | Not rated / administrative access | Self-grant and audit policy not verified in this pass | Review the intended admin authority and audit assertions |
| S9 | Not rated / validation | CLI and API email parity not tested | Validate supported addresses consistently |
| S10 | Prior report no longer matches current config | `compose.yaml` does not shadow bundled 2D assets; Dockerfile installs the release and runs as UID/GID 10001. | Fresh release artifact identity and installer integrity verification |

Pending: per-role authorization and object-level isolation coverage, full history secret scanning, package/image scan refresh, HTTPS proxy configuration, storage and log privacy, and scoped abuse-resistance review. Existing offline image findings remain open.
