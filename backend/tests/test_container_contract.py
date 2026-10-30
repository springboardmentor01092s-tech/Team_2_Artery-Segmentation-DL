"""Static packaging checks only; not a Docker build or deployment proof."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def test_container_has_nonroot_healthcheck_and_single_worker():
    source=(ROOT/'Dockerfile').read_text()
    assert 'USER 10001:10001' in source
    assert 'HEALTHCHECK' in source and '/api/health/ready' in source
    assert '"--workers", "1"' in source
    assert 'COPY --from=web /build/frontend/dist/' in source


def test_compose_keeps_private_mounts_and_local_binding():
    source=(ROOT/'compose.yaml').read_text()
    for requirement in ('127.0.0.1:8000:8000', 'read_only: true',
                        './models/trained_release:/models:ro',
                        'JWT_SECRET: ${JWT_SECRET:?', 'no-new-privileges:true',
                        'CV_LOCAL_DEMO_SESSIONS: "0"'):
        assert requirement in source


def test_build_context_excludes_credentials_data_and_checkpoints():
    excluded=set((ROOT/'.dockerignore').read_text().splitlines())
    assert {'**/.env','**/.env.*','**/*.db*','**/*.pt','**/*.pth',
            '**/*.ckpt','**/.git','**/node_modules','storage','models','data','Dataset'}<=excluded
