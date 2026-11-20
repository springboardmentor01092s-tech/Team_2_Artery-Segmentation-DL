set -eu
pgbin=/opt/homebrew/opt/postgresql@16/bin
rehearsal=$(mktemp -d /tmp/corovision-pg-api.XXXXXX)
trap '"$pgbin/pg_ctl" -D "$rehearsal/data" -m fast stop >/dev/null 2>&1 || true' EXIT
"$pgbin/initdb" -D "$rehearsal/data" --auth-local=trust --auth-host=reject -U corovision > "$rehearsal/initdb.log"
"$pgbin/pg_ctl" -D "$rehearsal/data" -l "$rehearsal/postgres.log" -o "-c listen_addresses= -k $rehearsal -p 55441" -w start
"$pgbin/createdb" -h "$rehearsal" -p 55441 -U corovision corovision_rehearsal_api
DATABASE_URL="postgresql+psycopg://corovision@/corovision_rehearsal_api?host=$rehearsal&port=55441" STORAGE_DIR="$rehearsal/storage" COROVISION_MODEL_PROVIDER=legacy COROVISION_INFERENCE_WORKER=0 PYTHONPATH=tests .venv/bin/python - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory

from pytest import MonkeyPatch
from app.database import engine
from test_review_reporting import test_review_run_binding_reports_exports_and_immutable_history

assert engine.url.get_backend_name() == "postgresql"
with MonkeyPatch.context() as patch, TemporaryDirectory() as root:
    test_review_run_binding_reports_exports_and_immutable_history(patch, Path(root))
engine.dispose()
print("PASS: PostgreSQL API report persistence, four exports, access denial and immutable history")
PY
pg() {
    utility=$1
    shift
    "$pgbin/$utility" -h "$rehearsal" -p 55441 -U corovision "$@"
}
pg pg_dump -Fc -f "$rehearsal/report.dump" corovision_rehearsal_api
pg createdb corovision_rehearsal_restored
pg pg_restore --exit-on-error -d corovision_rehearsal_restored "$rehearsal/report.dump"
for db in corovision_rehearsal_api corovision_rehearsal_restored; do
    pg psql -XAt -v ON_ERROR_STOP=1 "$db" -c 'SELECT to_jsonb(r) FROM research_reports r ORDER BY id' > "$rehearsal/$db.jsonl"
done
test -s "$rehearsal/corovision_rehearsal_api.jsonl"
cmp "$rehearsal/corovision_rehearsal_api.jsonl" "$rehearsal/corovision_rehearsal_restored.jsonl"
shasum -a 256 "$rehearsal/corovision_rehearsal_restored.jsonl"
echo "PASS: nonempty source and restored report snapshot rows match byte for byte"
printf 'Disposable rehearsal logs: %s\n' "$rehearsal"
