# API and regression results

- Full backend suite in the existing macOS AI-enabled virtualenv with a temporary SQLite database and storage directory: **338 passed, 5 skipped, 51 warnings** in 77.64 s. No collection failure in this profile. Base-only clean collection remains untested. `pypdf` is declared in base requirements; torch/torchvision and scipy are in AI requirements, and the legacy detector test imports torch during collection.
- Run `python3 audit_tests/inspect_contract.py http://127.0.0.1:8003` from the checkout. Root and readiness returned HTTP 200, public OpenAPI enumerated 125 operations. This inventories the API; it does not verify every operation or response schema.
- Pending: complete operation-by-role matrix, fixture-based workflow and output reconciliation, queue/restart and concurrency checks on an immutable build.
