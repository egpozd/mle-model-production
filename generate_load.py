import argparse, json, random, time, urllib.request, urllib.error
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--url', default='http://127.0.0.1:8000')
p.add_argument('--count', type=int, default=100, help='0 — непрерывно')
p.add_argument('--rate', type=float, default=2)
p.add_argument('--invalid-ratio', type=float, default=0.1)
a=p.parse_args()
if not 0 < a.rate <= 20 or a.count < 0 or not 0 <= a.invalid_ratio <= 1: p.error('Недопустимые параметры')
base=json.loads(Path(__file__).with_name('example.json').read_text())
i=0
try:
 while a.count==0 or i<a.count:
  data=dict(base, user_id=i, floor=random.randint(1,18), total_area=random.uniform(65,100))
  if random.random()<a.invalid_ratio: data['total_area']=-1
  request=urllib.request.Request(a.url+'/predict',json.dumps(data).encode(),{'Content-Type':'application/json'})
  try:
   with urllib.request.urlopen(request,timeout=20) as r: print(i,r.status)
  except urllib.error.HTTPError as e: print(i,e.code)
  i+=1;time.sleep(1/a.rate)
except KeyboardInterrupt: pass
