import sqlite3
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# --- НАСТРОЙКИ ---
SECRET_TOKEN = "my_super_secret_token_2026"
DB_NAME = "iot_data.db"

app = FastAPI(title="Sensor Data API")


# --- МОДЕЛЬ ДАННЫХ ---
class SensorData(BaseModel):
    temperature: float = Field(..., description="Температура")
    humidity: float = Field(..., description="Влажность")
    pressure: float = Field(..., description="Давление")
    recorded_at: str = Field(..., description="Дата и время в формате ISO 8601")


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


# --- API ENDPOINTS (защищены токеном) ---
@app.post("/api/v1/sensors", status_code=201)
def add_sensor_data(data: SensorData, _token: str = Depends(verify_token)):
    try:
        datetime.fromisoformat(data.recorded_at)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты")

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sensor_readings (temperature, humidity, pressure, recorded_at)
            VALUES (?, ?, ?, ?)
        ''', (data.temperature, data.humidity, data.pressure, data.recorded_at))
        conn.commit()
        new_id = cursor.lastrowid

    return {"status": "success", "message": "Данные успешно сохранены", "id": new_id}


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


# --- НОВЫЙ ENDPOINT: Получение всех данных в JSON (открытый доступ) ---
@app.get("/api/v1/sensors/all")
def get_all_data(limit: Optional[int] = 100):
    """Возвращает последние N записей (по умолчанию 100)"""
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sensor_readings ORDER BY id DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
    return [dict(row) for row in rows]


# --- НОВЫЙ ENDPOINT: Веб-интерфейс (открытый доступ) ---
@app.get("/", response_class=HTMLResponse)
def web_dashboard():
    """Главная страница с красивым дашбордом"""
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Получаем все записи, отсортированные по дате (новые сверху)
        cursor.execute('SELECT * FROM sensor_readings ORDER BY recorded_at DESC')
        rows = cursor.fetchall()

        # Считаем статистику
        cursor.execute('SELECT COUNT(*) as cnt FROM sensor_readings')
        total_count = cursor.fetchone()['cnt']

        # Последние показания для карточек
        cursor.execute('SELECT * FROM sensor_readings ORDER BY id DESC LIMIT 1')
        latest = cursor.fetchone()

    # Формируем строки таблицы
    table_rows = ""
    for row in rows:
        table_rows += f"""
        <tr>
            <td>{row['id']}</td>
            <td class="temp">{row['temperature']:.1f} °C</td>
            <td class="hum">{row['humidity']:.1f} %</td>
            <td class="press">{row['pressure']:.1f} hPa</td>
            <td>{row['recorded_at']}</td>
        </tr>
        """

    # Карточки с последними показаниями
    if latest:
        cards_html = f"""
        <div class="cards">
            <div class="card temp-card">
                <div class="card-title">🌡️ Температура</div>
                <div class="card-value">{latest['temperature']:.1f} °C</div>
                <div class="card-time">{latest['recorded_at']}</div>
            </div>
            <div class="card hum-card">
                <div class="card-title">💧 Влажность</div>
                <div class="card-value">{latest['humidity']:.1f} %</div>
                <div class="card-time">{latest['recorded_at']}</div>
            </div>
            <div class="card press-card">
                <div class="card-title">🎯 Давление</div>
                <div class="card-value">{latest['pressure']:.1f} hPa</div>
                <div class="card-time">{latest['recorded_at']}</div>
            </div>
        </div>
        """
    else:
        cards_html = '<div class="empty">📭 Нет данных. Отправьте показания через API.</div>'

    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sensor Dashboard</title>
        <meta http-equiv="refresh" content="30">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
                color: #333;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            header {{
                text-align: center;
                color: white;
                margin-bottom: 30px;
            }}
            header h1 {{
                font-size: 2.5em;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            }}
            header p {{
                font-size: 1.1em;
                opacity: 0.9;
            }}
            .stats {{
                background: rgba(255,255,255,0.2);
                padding: 10px 20px;
                border-radius: 20px;
                display: inline-block;
                color: white;
                margin-top: 15px;
                backdrop-filter: blur(10px);
            }}
            .cards {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .card {{
                background: white;
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                text-align: center;
                transition: transform 0.3s;
            }}
            .card:hover {{
                transform: translateY(-5px);
            }}
            .card-title {{
                font-size: 1em;
                color: #666;
                margin-bottom: 10px;
            }}
            .card-value {{
                font-size: 2.5em;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .card-time {{
                font-size: 0.85em;
                color: #999;
            }}
            .temp-card .card-value {{ color: #e74c3c; }}
            .hum-card .card-value {{ color: #3498db; }}
            .press-card .card-value {{ color: #9b59b6; }}
            .table-container {{
                background: white;
                border-radius: 15px;
                padding: 25px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                overflow-x: auto;
            }}
            .table-container h2 {{
                margin-bottom: 20px;
                color: #333;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #eee;
            }}
            th {{
                background: #f8f9fa;
                font-weight: 600;
                color: #555;
                position: sticky;
                top: 0;
            }}
            tr:hover {{
                background: #f8f9fa;
            }}
            .temp {{ color: #e74c3c; font-weight: 600; }}
            .hum {{ color: #3498db; font-weight: 600; }}
            .press {{ color: #9b59b6; font-weight: 600; }}
            .empty {{
                background: white;
                padding: 40px;
                border-radius: 15px;
                text-align: center;
                font-size: 1.2em;
                color: #666;
            }}
            footer {{
                text-align: center;
                color: white;
                margin-top: 30px;
                opacity: 0.8;
                font-size: 0.9em;
            }}
            @media (max-width: 600px) {{
                header h1 {{ font-size: 1.8em; }}
                .card-value {{ font-size: 2em; }}
                th, td {{ padding: 8px; font-size: 0.9em; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🌡️ Sensor Dashboard</h1>
                <p>Мониторинг показаний датчиков в реальном времени</p>
                <div class="stats">📊 Всего записей: <strong>{total_count}</strong></div>
            </header>

            {cards_html}

            <div class="table-container">
                <h2>📋 История показаний</h2>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Температура</th>
                            <th>Влажность</th>
                            <th>Давление</th>
                            <th>Дата и время</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows if table_rows else '<tr><td colspan="5" style="text-align:center; padding:30px;">Нет данных</td></tr>'}
                    </tbody>
                </table>
            </div>

            <footer>
                <p>Автообновление каждые 30 секунд • Открытый доступ</p>
            </footer>
        </div>
    </body>
    </html>
    """
    return html
