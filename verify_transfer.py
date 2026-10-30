import sys, json, cloudpickle, hashlib
from pathlib import Path
import pandas as pd
root=Path.cwd(); src=Path('C:/Users/egpoz/mle-mlflow-runtime/artifacts/real_estate_model_improvement/52b6764852554b4eb42d49cc5106430a/artifacts/model')
sys.path.insert(0,str(root/'services/models/v4/code'))
e=json.loads((src/'input_example.json').read_text()); X=pd.DataFrame(e['data'],columns=e['columns'])
with (src/'model.pkl').open('rb') as f: a=cloudpickle.load(f)
with (root/'services/models/v4/model.pkl').open('rb') as f: b=cloudpickle.load(f)
x=a.predict(X); y=b.predict(X)
result={'rows':len(X),'max_abs_difference':float(abs(x-y).max()),'predictions':y.tolist(),'sha256_equal':hashlib.sha256((src/'model.pkl').read_bytes()).digest()==hashlib.sha256((root/'services/models/v4/model.pkl').read_bytes()).digest()}
print(json.dumps(result)); (root/'model_verification.json').write_text(json.dumps(result,indent=2))
