import os, sys, json, logging, math
from pathlib import Path
from contextlib import asynccontextmanager
import cloudpickle
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
ROOT = Path(__file__).resolve().parents[2]
MODEL = Path(os.getenv("MODEL_PATH", str(ROOT / "services/models/v4")))
sys.path.insert(0, str(MODEL / "code"))
EXAMPLE = json.loads((ROOT / "example.json").read_text())
COUNT = Counter("real_estate_predictions", "Количество прогнозов", ["status"])
LATENCY = Histogram("real_estate_prediction_seconds", "Время работы модели")
PRICES = Histogram("real_estate_price_rubles", "Прогноз цены", buckets=(1e6,3e6,5e6,1e7,2e7,5e7,1e8,5e8))
class Request(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False, json_schema_extra={"example": EXAMPLE})
    user_id: int = Field(ge=0)
    floor: int = Field(ge=1)
    kitchen_area: float = Field(ge=0)
    living_area: float = Field(ge=0)
    rooms: int = Field(ge=0, le=100)
    is_apartment: bool
    total_area: float = Field(gt=0, le=10000)
    build_year: int = Field(ge=1000, le=2100)
    building_type_int: int = Field(ge=0)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    ceiling_height: float = Field(gt=0, le=20)
    flats_count: int = Field(ge=0)
    floors_total: int = Field(ge=1)
    has_elevator: bool
    @model_validator(mode="after")
    def coherent(self):
        if self.floor > self.floors_total:
            raise ValueError("Этаж превышает этажность дома")
        if self.living_area + self.kitchen_area > self.total_area:
            raise ValueError("Сумма площадей превышает общую площадь")
        return self
class Response(BaseModel):
    user_id: int
    prediction: float
class Handler:
    def __init__(self):
        with (MODEL / "model.pkl").open("rb") as f:
            self.model = cloudpickle.load(f)
    def predict(self, request):
        try:
            with LATENCY.time():
                value = float(self.model.predict(pd.DataFrame([request.model_dump(exclude={"user_id"})]))[0])
                if not math.isfinite(value):
                    raise ValueError("Nonfinite prediction")
            COUNT.labels("success").inc()
            PRICES.observe(value)
            return Response(user_id=request.user_id, prediction=value)
        except Exception:
            COUNT.labels("error").inc()
            logging.exception("Ошибка прогноза")
            raise HTTPException(500, "Не удалось получить прогноз") from None
@asynccontextmanager
async def lifespan(app):
    app.state.handler = Handler()
    yield
app = FastAPI(title="Оценка недвижимости V4", lifespan=lifespan)
Instrumentator().instrument(app).expose(app)
@app.get("/health")
def health():
    return {"status": "ok", "model": "V4"}
@app.post("/predict", response_model=Response)
def predict(request: Request):
    return app.state.handler.predict(request)
