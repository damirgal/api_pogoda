import sqlite3
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# --- НАСТРОЙКИ ---
SECRET_TOKEN = "my_super_secret_token_2026"  # Замените на ваш секретный токен
DB_NAME = "iot_data.db"

app = FastAPI(title="Sensor Data API")

# --- МОДЕЛЬ ДАННЫХ ---
class SensorData(BaseModel):
    temperature: float = Field(..., description="Температура")
    humidity: float = Field(..., description="Влажность")
    pressure: float = Field(..., description="Давление")
    recorded_at: str = Field(..., description="Дата и время в формате ISO 8601 (например, 2026-07-04T15:30:00)")

# --- ИНИЦИАЛИЗАЦИЯ БД ---
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                temperature REAL NOT NULL,
                humidity REAL NOT NULL,
                pressure REAL NOT NULL,
                recorded_at TEXT NOT NULL
            )
        ''')
        conn.commit()

init_db()

# --- ПРОВЕРКА ТОКЕНА ---
def verify_token(x_api_token: str = Header(..., alias="X-API-Token")):
    if x_api_token != SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Неверный или отсутствующий токен доступа")

# --- ENDPOINT ---
@app.post("/api/v1/sensors", status_code=201)
def add_sensor_data(data: SensorData, _token: str = Depends(verify_token)):
    # Проверяем формат даты (опционально, но полезно для валидации)
    try:
        datetime.fromisoformat(data.recorded_at)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты. Используйте ISO 8601 (YYYY-MM-DDTHH:MM:SS)")

    # Сохраняем в БД
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sensor_readings (temperature, humidity, pressure, recorded_at)
            VALUES (?, ?, ?, ?)
        ''', (data.temperature, data.humidity, data.pressure, data.recorded_at))
        conn.commit()
        new_id = cursor.lastrowid

    return {"status": "success", "message": "Данные успешно сохранены", "id": new_id}

# --- ДОПОЛНИТЕЛЬНЫЙ ENDPOINT (для проверки, что данные записались) ---
@app.get("/api/v1/sensors/latest")
def get_latest_data(_token: str = Depends(verify_token)):
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sensor_readings ORDER BY id DESC LIMIT 1')
        row = cursor.fetchone()
        
    if row:
        return dict(row)
    raise HTTPException(status_code=404, detail="Данные еще не поступали")