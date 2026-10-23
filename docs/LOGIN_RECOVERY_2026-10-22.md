# Local login recovery

Login failed because no backend was listening on 127.0.0.1:8000. The prior
environment stalled during dependency imports; accounts/passwords were not the
cause. The original environment and database were preserved.

A separate temporary runtime was created at
`/tmp/corovision-login-recovery-20261022`, installing the declared
`backend/requirements.txt`. The backend was started with:

```sh
/tmp/corovision-login-recovery-20261022/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

This runtime is temporary and may be removed by OS cleanup/reboot. It does not
replace the existing virtual environment or establish inference/training package
parity. No training was started. No accounts, passwords or permissions changed.

Verification: backend startup completed; actual Demo Radiologist sign-in reached
the authenticated dashboard in Chrome. Notification bulk-action and RBAC tests
passed (4 tests) in isolated test storage. A Starlette test-client deprecation
warning and the existing short test-only JWT-secret warning remain.
