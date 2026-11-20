"""Execute the nine controlled fixtures without altering original results."""
import json
from pathlib import Path
from phantom_geometry import measure

kinds=('straight','curved','tapered','branch','eccentric','two-lesions',
       'boundary-perturbation','blur-noise','low-contrast')
rows=[]
for kind in kinds:
    baseline=measure(kind)
    local=measure(kind,local_measurement=True)
    rows.append(dict(fixture=kind,original_adapter=baseline,candidate_local=local))
output=Path(__file__).with_name('NINE_PHANTOM_LOCAL_RESULTS.json')
output.write_text(json.dumps({'scope':'Synthetic declared paths and candidate regions; not automatic anatomical association',
    'rows':rows},indent=2))
print(json.dumps([{'fixture':r['fixture'],'status':r['candidate_local']['status'],
    'reasons':r['candidate_local']['reasons'],
    'narrowing':r['candidate_local'].get('narrowing_percent')} for r in rows],indent=2))
