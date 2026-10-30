from fastapi.testclient import TestClient
from services.ml_service.app import app, EXAMPLE

def test_api():
    with TestClient(app) as c:
        assert c.get('/health').status_code == 200
        r=c.post('/predict',json=EXAMPLE)
        assert r.status_code == 200
        assert set(r.json()) == {'user_id','prediction'}
        assert r.json()['prediction'] > 0
        assert c.post('/predict',json={}).status_code == 422
        assert c.post('/predict',json=dict(EXAMPLE,total_area=-1)).status_code == 422
        assert c.post('/predict',json=dict(EXAMPLE,floor='17')).status_code == 422
        assert 'real_estate_price_rubles_bucket' in c.get('/metrics').text
        assert c.get('/docs').status_code == 200

def test_prediction_failure(monkeypatch):
    with TestClient(app) as c:
        def fail(*args):
            raise RuntimeError('private path and secrets')
        monkeypatch.setattr(app.state.handler.model, 'predict', fail)
        r=c.post('/predict',json=EXAMPLE)
        assert r.status_code == 500
        assert 'private' not in r.text

def test_reference_prediction():
    with TestClient(app) as c:
        value=c.post('/predict',json=EXAMPLE).json()['prediction']
        assert abs(value - 14665857.686491901) < 0.001

def test_validation_boundaries():
    with TestClient(app) as c:
        for changes in ({'floor':19}, {'living_area':1000.0}, {'latitude':91.0}, {'unexpected':1}, {'has_elevator':1}):
            assert c.post('/predict',json=dict(EXAMPLE,**changes)).status_code == 422
        schema=c.get('/openapi.json').json()
        assert schema['components']['schemas']['Request']['example'] == EXAMPLE
        metrics=c.get('/metrics').text
        assert '# TYPE real_estate_predictions_total counter' in metrics
        assert '# TYPE real_estate_prediction_seconds histogram' in metrics
