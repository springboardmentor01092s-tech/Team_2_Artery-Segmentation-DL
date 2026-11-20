# Local release testing — 20 November 2026

This is local, disposable Docker evidence. It is not evidence of a hosted
deployment, clinical validation, or a production security certification.

## Results

| Area | Result | Evidence |
| --- | --- | --- |
| First-admin and administrator MFA | PASS, local Docker/browser scope | Chromium created the initial administrator, enrolled a TOTP factor, rejected reuse, and retained the factor after restart. |
| Invitation-only registration | PASS, local Docker/browser scope | An administrator created an email-bound invitation; the invited Viewer redeemed it once. An outsider could not create invitations. |
| Browser credential storage | PASS, tested scope | The browser probe found no legacy `localStorage` access token after administrator login or invitation redemption. Tokens are tab-session scoped. |
| API access-control smoke checks | PASS, tested scope | Required no-store, no-sniff, frame-denial, and referrer headers were present. Anonymous protected routes returned 401 or 403. |
| API contract and regression | PASS | Generated OpenAPI contains 111 paths including login and invitation routes. Full backend suite: 333 passed, 5 skipped. Frontend Node suite: 20 passed. |
| Bounded liveness load | PASS, not inference capacity | Twenty `/api/health/live` requests at 1, 4, and 8 clients all succeeded. Observed p95 was 2.140, 2.595, and 7.479 ms respectively. |
| Lighthouse login audit | PARTIAL | Lighthouse 12.8.2 completed without a runtime error: accessibility 0.96, performance 0.64, FCP 4.4 s, LCP 11.4 s, TBT 0 ms, CLS 0. The cold local Docker login route needs performance investigation before claiming a production performance pass. |

## Reproduction materials

- `admin_access_20261120/browser_probe.py` and `browser_probe.log`: browser/first-admin acceptance.
- `release_testing_20261120/http_probe.py` and `http.json`: header, anonymous-route, and bounded liveness checks.
- `release_testing_20261120/openapi.json`: generated contract snapshot.
- `release_testing_20261120/lighthouse-login.json`: full Lighthouse result.
- `release_testing_20261120/image.txt`: tested disposable image reference.
- `release-pytest.log`: complete backend regression output.

## Explicit limits and next evidence

This test did not use a public target, TLS termination, a clean clone of the
unpublished working tree, a dynamic security scanner, or real inference load.
Before hosted acceptance, choose and authorize a deployment target, build from
a reviewed source revision, resolve or formally accept remaining container
findings, repeat authenticated export and role workflows over HTTPS, and run a
capacity test representing the chosen host.
