# Phase 6 — Reproducible packaging

Frontend uses committed package-lock.json and npm ci. Backend range requirements
remain, with new exact `backend/constraints-tested-macos-py313.txt` capturing the
observed Python 3.13/macOS arm64 environment. It is a version constraint snapshot,
not a hash-locked wheel repository, clean-install proof or Linux lock.

On an equivalent reviewed platform, install requirements-ai.txt together with
the constraint file. Keep deployment secrets server-side and outside Git. Configure
DATABASE_URL, STORAGE_DIR, JWT_SECRET, CORS_ORIGINS, model-provider/release paths
and worker flags explicitly. Production requires a private >=32-byte JWT secret
and demo sessions/sharing disabled. Never ship local accounts, DB, datasets or
private uploads in a container.

Existing Dockerfile has separate Node build/non-root Python runtime, CPU inference
dependencies, healthcheck and one worker. Compose mounts checkpoints read-only,
persists data, binds loopback, drops capabilities and sets a read-only filesystem.
Three static configuration tests passed previously and in the current full suite.
Docker executable is absent: no image build, Linux dependency resolution,
clean-machine startup or container recovery test was executed. Base-image tags
and Linux Python requirements are not digest/hash-locked. Do not apply the macOS
constraint file blindly to the CPU Linux image. Resolve and lock on that target.

Checkpoint installation remains hash-verified via existing manifests. Preserve
the model-specific preprocessing, dimensions, orientation, thresholds and label
mapping in every run; optional enhanced preprocessing is not baseline parity.
Current ARCADE frozen comparison references threshold 0.5 and the unchanged
512-grid checkpoint, not a newly approved advanced model.

Remaining release gates: target Linux lock/wheel hashes and image digests; actual
Docker build/start/health; model mount and missing-model failure checks; synthetic
backup restore then target deployment drill; documented operator cutover and
rollback. No deployment or Git push was performed by this audit.
