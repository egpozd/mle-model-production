import json,urllib.request,urllib.error
from pathlib import Path
out={}
for port in (8000,8001,8002):
 base=f'http://localhost:{port}'; checks={}
 for path in ('/health','/docs','/metrics','/openapi.json'):
  with urllib.request.urlopen(base+path,timeout=15) as r: checks[path]=r.status
 req=urllib.request.Request(base+'/predict',Path('example.json').read_bytes(),{'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=15) as r: checks['prediction']=json.load(r)
 try: urllib.request.urlopen(urllib.request.Request(base+'/predict',b'{}',{'Content-Type':'application/json'}))
 except urllib.error.HTTPError as e: checks['invalid']=e.code
 assert checks['invalid']==422 and abs(checks['prediction']['prediction']-14665857.686491901)<.001
 out[str(port)]=checks
Path('http_verification.json').write_text(json.dumps(out,indent=2))
print(out)
