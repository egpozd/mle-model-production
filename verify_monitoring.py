import json,urllib.request,urllib.parse,base64,time
from pathlib import Path
out={}
for panel in json.loads(Path('dashboard.json').read_text(encoding='utf-8'))['panels']:
 q=urllib.parse.urlencode({'query':panel['targets'][0]['expr'],'time':time.time()})
 with urllib.request.urlopen('http://localhost:9090/api/v1/query?'+q) as r: out[panel['title']]=json.load(r)
req=urllib.request.Request('http://localhost:3000/api/dashboards/uid/real-estate',headers={'Authorization':'Basic '+base64.b64encode(b'admin:student-local').decode()})
with urllib.request.urlopen(req) as r: out['grafana_dashboard']=json.load(r)['meta']
Path('monitoring_verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
assert all(v['status']=='success' and v['data']['result'] for k,v in out.items() if k != 'grafana_dashboard')
print({k:v.get('status','loaded') for k,v in out.items()})
