"""Small read-only localhost HTTP benchmark; never inference or training."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import subprocess
import time
from urllib.request import urlopen


def sample(pid):
    if pid is None:return None
    row=subprocess.run(['ps','-p',str(pid),'-o','rss=,%cpu='],capture_output=True,text=True,check=True).stdout.split()
    return dict(rss_kib=int(row[0]),cpu_percent=float(row[1]),scope='instantaneous ps sample; not peak utilization')


def request(_):
    began=time.perf_counter()
    try:
        with urlopen('http://127.0.0.1:8000/api/health/live',timeout=10) as response:
            body=response.read()
            return dict(seconds=time.perf_counter()-began,status=response.status,bytes=len(body))
    except Exception as error:
        return dict(seconds=time.perf_counter()-began,status=None,error=type(error).__name__)


def run(pid=None):
    result=dict(created_at=datetime.now(timezone.utc).isoformat(),platform=platform.platform(),
                endpoint='/api/health/live',before=sample(pid),batches=[],
                inference_latency=None,gpu_usage=None,storage_growth=None,
                limitations=['Only 60 public liveness GETs; not inference capacity, authentication, database throughput or clinical readiness.',
                             'RSS/CPU are samples, not peaks. No GPU benchmark or uploaded-data growth test.'])
    for workers in (1,4,8):
        start=time.perf_counter()
        with ThreadPoolExecutor(max_workers=workers) as pool:rows=list(pool.map(request,range(20)))
        wall=time.perf_counter()-start;durations=sorted(row['seconds'] for row in rows)
        result['batches'].append(dict(concurrency=workers,requests=20,success=sum(r['status']==200 for r in rows),
            wall_seconds=wall,requests_per_second=20/wall,p50_ms=durations[9]*1000,p95_ms=durations[18]*1000,
            max_ms=durations[-1]*1000,responses=rows))
    result['after']=sample(pid)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--pid',type=int);args=parser.parse_args()
    if args.pid is not None and args.pid<=0:parser.error('PID must be positive')
    if args.out.exists():parser.error('Output already exists; never overwrite benchmark history')
    result=run(args.pid);args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x') as stream:json.dump(result,stream,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k!='batches'}))
    print(json.dumps([dict((k,v) for k,v in b.items() if k!='responses') for b in result['batches']]))
