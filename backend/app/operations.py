"""Single-process operational telemetry. No patient identifiers, bodies or tokens."""
from collections import defaultdict
import json
import logging
import os
import re
import threading
import time
from uuid import uuid4

logger = logging.getLogger('corovision.operations')
STARTED = time.monotonic()
COUNTERS = defaultdict(lambda: {'requests': 0, 'errors': 0, 'seconds': 0., 'max_seconds': 0.})
LOCK = threading.Lock()


def validate_deployment_environment():
    if os.getenv('COROVISION_ENV', 'development') != 'production':
        return
    secret = os.getenv('JWT_SECRET', '')
    if len(secret.encode()) < 32 or secret.lower().startswith(('development', 'change', 'replace')):
        raise RuntimeError('Production requires a private, randomly generated JWT_SECRET of at least 32 bytes')
    if any(os.getenv(name, '0') == '1' for name in ('CV_LOCAL_DEMO_SESSIONS', 'CV_LOCAL_DEMO_SHARING')):
        raise RuntimeError('Local demo session/sharing flags must be disabled for production')


def install_telemetry(app):
    @app.middleware('http')
    async def telemetry(request, call_next):
        request_id = uuid4().hex  # Never trust a user-supplied correlation identifier in logs.
        started, status = time.monotonic(), 500
        try:
            response = await call_next(request)
            status = response.status_code
            response.headers['X-Request-ID'] = request_id
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['Referrer-Policy'] = 'no-referrer'
            response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
            if request.url.path.startswith('/api/'):
                response.headers['Cache-Control'] = 'no-store'
            return response
        finally:
            elapsed = time.monotonic() - started
            route = getattr(request.scope.get('route'), 'path', 'unmatched')
            # Route templates, not raw URLs/queries/filenames/user IDs.
            if not re.fullmatch(r'[/a-zA-Z0-9_{}:.\-]*', route):
                route = 'other'
            key = (request.method, route, status // 100)
            with LOCK:
                item = COUNTERS[key]
                item['requests'] += 1
                item['errors'] += status >= 500
                item['seconds'] += elapsed
                item['max_seconds'] = max(item['max_seconds'], elapsed)
            logger.info(json.dumps({'event': 'http_request', 'request_id': request_id,
                                   'method': request.method, 'route': route,
                                   'status': status, 'duration_ms': round(elapsed*1000, 2)}))


def telemetry_snapshot():
    with LOCK:
        rows = [{'method': key[0], 'route': key[1], 'status_class': key[2], **value}
                for key, value in sorted(COUNTERS.items())]
    return {'scope': 'Current single API process; resets on restart',
            'uptime_seconds': round(time.monotonic()-STARTED, 2), 'routes': rows}


def prometheus(snapshot):
    rows = ['# HELP corovision_http_requests_total HTTP requests in this API process.',
            '# TYPE corovision_http_requests_total counter',
            '# TYPE corovision_http_request_duration_seconds_sum counter',
            '# TYPE corovision_process_uptime_seconds gauge',
            f'corovision_process_uptime_seconds {snapshot["uptime_seconds"]}']
    for row in snapshot['routes']:
        labels = f'method="{row["method"]}",route="{row["route"]}",status_class="{row["status_class"]}xx"'
        rows.extend([f'corovision_http_requests_total{{{labels}}} {row["requests"]}',
                     f'corovision_http_request_duration_seconds_sum{{{labels}}} {row["seconds"]:.6f}'])
    return '\n'.join(rows) + '\n'
