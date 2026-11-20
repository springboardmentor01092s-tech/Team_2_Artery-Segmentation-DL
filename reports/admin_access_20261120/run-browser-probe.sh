set -eu
JWT_SECRET=$(openssl rand -hex 32)
export JWT_SECRET
container=$(docker run --rm -d -p 127.0.0.1:18087:8000 -e JWT_SECRET corovision:auth-local-acceptance)
unset JWT_SECRET
trap 'docker stop -t 4 "$container" >/dev/null 2>&1 || true' EXIT
CV_PROBE_CONTAINER="$container" /opt/anaconda3/bin/python reports/admin_access_20261120/browser_probe.py
