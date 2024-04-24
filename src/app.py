import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import os

import sys  # Добавляем модуль sys

# Добавляем текущий каталог в PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Database class
import db_init

# Создаем экземпляр FastAPI
app = FastAPI()

# Load model
exp_path = os.path.join(os.getcwd(), "experiments")
model_path = os.path.join(exp_path, "log_reg.sav")
model = joblib.load(model_path)

# Initialize the database
db = db_init.Database()
db.create_database("lab2_bd")
db.create_table("predictions", {'X': 'String', 'y': 'String', 'predictions': 'String'})

# Define the Pydantic input data model
class InputData(BaseModel):
    X: list
    y: list

# Define the endpoint for predictions
@app.post("/predict/")
async def predict(input_data: InputData):
    try:
        X_values = []
        y_values = []

        # Извлекаем значения из всех образцов
        for i in range(len(input_data.X)):
            X_values.append([v for v in input_data.X[i].values()])
            y_values.append([v for v in input_data.y[i].values()])

        # Выполняем прогноз
        predictions = model.predict(pd.DataFrame(X_values))

        # Сохраняем прогнозы в базу данных с отметкой времени
        db.insert_data("predictions", X_values, y_values, predictions)

        # Формируем ответ
        response = {"predictions": predictions.tolist()}
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Swagger UI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html

@app.get("/docs", response_class=HTMLResponse)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="API docs")

@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    return JSONResponse(get_openapi(title="Your Project Name", version="0.1.0", routes=app.routes))
