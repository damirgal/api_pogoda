import sqlite3
from fastapi import FastAPI, HTTPException, Header, Depends, Query
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

# --- API: Получение данных с фильтрацией (открытый доступ) ---
@app.get("/api/v1/sensors/all")
def get_all_data(
    limit: Optional[int] = Query(100, ge=1, le=10000),
    from_date: Optional[str] = Query(None, description="Начальная дата (ISO 8601)"),
    to_date: Optional[str] = Query(None, description="Конечная дата (ISO 8601)")
):
    """
    Возвращает записи с возможностью фильтрации по диапазону дат.
    Если указаны from_date/to_date — лимит не применяется.
    Данные отсортированы по дате убывания (новые сверху).
    """
    query = "SELECT * FROM sensor_readings"
    params = []
    conditions = []

    if from_date:
        conditions.append("recorded_at >= ?")
        params.append(from_date)
    if to_date:
        conditions.append("recorded_at <= ?")
        params.append(to_date)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY recorded_at DESC"

    # Лимит применяем только если нет фильтра по датам
    if not (from_date or to_date):
        query += " LIMIT ?"
        params.append(limit)

    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

    return [dict(row) for row in rows]

# --- ВЕБ-ИНТЕРФЕЙС ---
@app.get("/", response_class=HTMLResponse)
def web_dashboard():
    html = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sensor Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
                color: #333;
            }
            .container { max-width: 1300px; margin: 0 auto; }
            header {
                text-align: center;
                color: white;
                margin-bottom: 25px;
            }
            header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            }
            header p { font-size: 1.1em; opacity: 0.9; }
            .stats {
                background: rgba(255,255,255,0.2);
                padding: 10px 20px;
                border-radius: 20px;
                display: inline-block;
                color: white;
                margin-top: 15px;
                backdrop-filter: blur(10px);
            }

            /* Карточки последних показаний */
            .cards {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 25px;
            }
            .card {
                background: white;
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                text-align: center;
                transition: transform 0.3s;
            }
            .card:hover { transform: translateY(-5px); }
            .card-title { font-size: 1em; color: #666; margin-bottom: 10px; }
            .card-value { font-size: 2.5em; font-weight: bold; margin-bottom: 10px; }
            .card-time { font-size: 0.85em; color: #999; }
            .temp-card .card-value { color: #e74c3c; }
            .hum-card .card-value { color: #3498db; }
            .press-card .card-value { color: #9b59b6; }

            /* Панель фильтров */
            .filters {
                background: white;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                margin-bottom: 25px;
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                align-items: flex-end;
            }
            .filter-group {
                display: flex;
                flex-direction: column;
                flex: 1;
                min-width: 180px;
            }
            .filter-group label {
                font-size: 0.85em;
                color: #666;
                margin-bottom: 5px;
                font-weight: 600;
            }
            .filter-group input {
                padding: 10px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 0.95em;
                transition: border-color 0.2s;
            }
            .filter-group input:focus {
                outline: none;
                border-color: #667eea;
            }
            .btn-group { display: flex; gap: 10px; flex-wrap: wrap; }
            button {
                padding: 10px 20px;
                border: none;
                border-radius: 8px;
                font-size: 0.95em;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
                white-space: nowrap;
            }
            .btn-primary {
                background: #667eea;
                color: white;
            }
            .btn-primary:hover { background: #5568d3; transform: translateY(-2px); }
            .btn-secondary {
                background: #e0e0e0;
                color: #333;
            }
            .btn-secondary:hover { background: #d0d0d0; }
            .btn-success {
                background: #27ae60;
                color: white;
            }
            .btn-success:hover { background: #219a52; transform: translateY(-2px); }

            /* Графики */
            .charts {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 20px;
                margin-bottom: 25px;
            }
            .chart-box {
                background: white;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            .chart-box h3 {
                margin-bottom: 15px;
                color: #333;
                font-size: 1.1em;
            }
            .chart-wrapper {
                position: relative;
                height: 250px;
            }

            /* Таблица */
            .table-container {
                background: white;
                border-radius: 15px;
                padding: 25px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                overflow-x: auto;
                margin-bottom: 25px;
            }
            .table-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                flex-wrap: wrap;
                gap: 10px;
            }
            .table-header h2 { color: #333; }
            .record-count {
                background: #f0f0f0;
                padding: 5px 15px;
                border-radius: 15px;
                font-size: 0.9em;
                color: #666;
            }
            table { width: 100%; border-collapse: collapse; }
            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #eee;
            }
            th {
                background: #f8f9fa;
                font-weight: 600;
                color: #555;
                position: sticky;
                top: 0;
            }
            tr:hover { background: #f8f9fa; }
            .temp { color: #e74c3c; font-weight: 600; }
            .hum { color: #3498db; font-weight: 600; }
            .press { color: #9b59b6; font-weight: 600; }

            /* Спиннер и сообщения */
            .loader {
                text-align: center;
                padding: 40px;
                color: #666;
                font-size: 1.1em;
            }
            .spinner {
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 15px;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .empty {
                background: white;
                padding: 40px;
                border-radius: 15px;
                text-align: center;
                font-size: 1.2em;
                color: #666;
            }
            footer {
                text-align: center;
                color: white;
                margin-top: 20px;
                opacity: 0.8;
                font-size: 0.9em;
            }
            @media (max-width: 600px) {
                header h1 { font-size: 1.8em; }
                .card-value { font-size: 2em; }
                th, td { padding: 8px; font-size: 0.9em; }
                .filters { flex-direction: column; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🌡️ Sensor Dashboard</h1>
                <p>Мониторинг показаний датчиков в реальном времени</p>
                <div class="stats">📊 Всего записей: <strong id="totalCount">—</strong></div>
            </header>

            <!-- Карточки последних показаний -->
            <div class="cards" id="latestCards">
                <div class="loader"><div class="spinner"></div>Загрузка...</div>
            </div>

            <!-- Фильтры -->
            <div class="filters">
                <div class="filter-group">
                    <label for="fromDate">📅 С даты</label>
                    <input type="datetime-local" id="fromDate">
                </div>
                <div class="filter-group">
                    <label for="toDate">📅 По дату</label>
                    <input type="datetime-local" id="toDate">
                </div>
                <div class="btn-group">
                    <button class="btn-primary" onclick="applyFilters()">🔍 Применить</button>
                    <button class="btn-secondary" onclick="resetFilters()">↺ Сбросить</button>
                    <button class="btn-success" onclick="exportCSV()">📥 Экспорт CSV</button>
                </div>
            </div>

            <!-- Графики -->
            <div class="charts">
                <div class="chart-box">
                    <h3>🌡️ Температура, °C</h3>
                    <div class="chart-wrapper"><canvas id="tempChart"></canvas></div>
                </div>
                <div class="chart-box">
                    <h3>💧 Влажность, %</h3>
                    <div class="chart-wrapper"><canvas id="humChart"></canvas></div>
                </div>
                <div class="chart-box">
                    <h3>🎯 Давление, hPa</h3>
                    <div class="chart-wrapper"><canvas id="pressChart"></canvas></div>
                </div>
            </div>

            <!-- Таблица -->
            <div class="table-container">
                <div class="table-header">
                    <h2>📋 История показаний</h2>
                    <span class="record-count" id="recordCount">0 записей</span>
                </div>
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
                    <tbody id="dataTable">
                        <tr><td colspan="5" class="loader"><div class="spinner"></div>Загрузка...</td></tr>
                    </tbody>
                </table>
            </div>

            <footer>
                <p>🔄 Автообновление каждые 30 секунд • Открытый доступ</p>
            </footer>
        </div>

        <script>
            let currentData = [];
            let charts = {};

            // Инициализация графиков
            function initCharts() {
                const commonOptions = {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { intersect: false, mode: 'index' },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: 'rgba(0,0,0,0.8)',
                            padding: 10,
                            titleFont: { size: 13 },
                            bodyFont: { size: 12 }
                        }
                    },
                    scales: {
                        x: {
                            type: 'time',
                            time: { tooltipFormat: 'dd.MM.yyyy HH:mm' },
                            ticks: { maxRotation: 45, autoSkip: true, maxTicksLimit: 8 }
                        },
                        y: { beginAtZero: false }
                    },
                    elements: {
                        point: { radius: 3, hoverRadius: 6 },
                        line: { tension: 0.3 }
                    }
                };

                charts.temp = new Chart(document.getElementById('tempChart'), {
                    type: 'line',
                    data: { datasets: [{ data: [], borderColor: '#e74c3c', backgroundColor: 'rgba(231,76,60,0.1)', fill: true }] },
                    options: { ...commonOptions, scales: { ...commonOptions.scales, y: { ...commonOptions.scales.y, title: { display: true, text: '°C' } } } }
                });
                charts.hum = new Chart(document.getElementById('humChart'), {
                    type: 'line',
                    data: { datasets: [{ data: [], borderColor: '#3498db', backgroundColor: 'rgba(52,152,219,0.1)', fill: true }] },
                    options: { ...commonOptions, scales: { ...commonOptions.scales, y: { ...commonOptions.scales.y, title: { display: true, text: '%' } } } }
                });
                charts.press = new Chart(document.getElementById('pressChart'), {
                    type: 'line',
                    data: { datasets: [{ data: [], borderColor: '#9b59b6', backgroundColor: 'rgba(155,89,182,0.1)', fill: true }] },
                    options: { ...commonOptions, scales: { ...commonOptions.scales, y: { ...commonOptions.scales.y, title: { display: true, text: 'hPa' } } } }
                });
            }

            // Загрузка последних показаний для карточек
            async function loadLatest() {
                try {
                    const resp = await fetch('/api/v1/sensors/all?limit=1');
                    const data = await resp.json();
                    const container = document.getElementById('latestCards');

                    if (data.length === 0) {
                        container.innerHTML = '<div class="empty">📭 Нет данных. Отправьте показания через API.</div>';
                        return;
                    }

                    const d = data[0];
                    container.innerHTML = `
                        <div class="card temp-card">
                            <div class="card-title">🌡️ Температура</div>
                            <div class="card-value">${d.temperature.toFixed(1)} °C</div>
                            <div class="card-time">${formatDate(d.recorded_at)}</div>
                        </div>
                        <div class="card hum-card">
                            <div class="card-title">💧 Влажность</div>
                            <div class="card-value">${d.humidity.toFixed(1)} %</div>
                            <div class="card-time">${formatDate(d.recorded_at)}</div>
                        </div>
                        <div class="card press-card">
                            <div class="card-title">🎯 Давление</div>
                            <div class="card-value">${d.pressure.toFixed(1)} hPa</div>
                            <div class="card-time">${formatDate(d.recorded_at)}</div>
                        </div>
                    `;
                } catch (e) {
                    console.error('Ошибка загрузки последних данных:', e);
                }
            }

            // Загрузка данных с фильтрами
            async function loadData() {
                const from = document.getElementById('fromDate').value;
                const to = document.getElementById('toDate').value;

                let url = '/api/v1/sensors/all?';
                if (from) url += `from_date=${encodeURIComponent(from.replace('T', ' '))}:00&`;
                if (to) url += `to_date=${encodeURIComponent(to.replace('T', ' '))}:59&`;
                if (!from && !to) url += 'limit=500&';

                try {
                    const resp = await fetch(url);
                    currentData = await resp.json();
                    renderTable(currentData);
                    renderCharts(currentData);
                    document.getElementById('recordCount').textContent = `${currentData.length} записей`;
                } catch (e) {
                    console.error('Ошибка загрузки данных:', e);
                    document.getElementById('dataTable').innerHTML =
                        '<tr><td colspan="5" style="text-align:center;color:#e74c3c;">Ошибка загрузки данных</td></tr>';
                }
            }

            // Рендер таблицы (данные уже отсортированы по убыванию с сервера)
            function renderTable(data) {
                const tbody = document.getElementById('dataTable');
                if (data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:30px;">Нет данных по выбранным фильтрам</td></tr>';
                    return;
                }
                tbody.innerHTML = data.map(d => `
                    <tr>
                        <td>${d.id}</td>
                        <td class="temp">${d.temperature.toFixed(1)} °C</td>
                        <td class="hum">${d.humidity.toFixed(1)} %</td>
                        <td class="press">${d.pressure.toFixed(1)} hPa</td>
                        <td>${formatDate(d.recorded_at)}</td>
                    </tr>
                `).join('');
            }

            // Рендер графиков (данные сортируем по возрастанию для оси X)
            function renderCharts(data) {
                const sorted = [...data].sort((a, b) => new Date(a.recorded_at) - new Date(b.recorded_at));
                const points = sorted.map(d => ({ x: d.recorded_at.replace(' ', 'T'), y: d.temperature }));
                const humPoints = sorted.map(d => ({ x: d.recorded_at.replace(' ', 'T'), y: d.humidity }));
                const pressPoints = sorted.map(d => ({ x: d.recorded_at.replace(' ', 'T'), y: d.pressure }));

                charts.temp.data.datasets[0].data = points;
                charts.hum.data.datasets[0].data = humPoints;
                charts.press.data.datasets[0].data = pressPoints;

                charts.temp.update();
                charts.hum.update();
                charts.press.update();
            }

            // Форматирование даты для отображения
            function formatDate(isoStr) {
                const d = new Date(isoStr.replace(' ', 'T'));
                return d.toLocaleString('ru-RU', {
                    day: '2-digit', month: '2-digit', year: 'numeric',
                    hour: '2-digit', minute: '2-digit'
                });
            }

            // Применение фильтров
            function applyFilters() {
                loadData();
            }

            // Сброс фильтров
            function resetFilters() {
                document.getElementById('fromDate').value = '';
                document.getElementById('toDate').value = '';
                loadData();
            }

            // Экспорт в CSV
            function exportCSV() {
                if (currentData.length === 0) {
                    alert('Нет данных для экспорта');
                    return;
                }
                const headers = ['ID', 'Температура (°C)', 'Влажность (%)', 'Давление (hPa)', 'Дата и время'];
                const rows = currentData.map(d => [
                    d.id,
                    d.temperature.toFixed(2),
                    d.humidity.toFixed(2),
                    d.pressure.toFixed(2),
                    d.recorded_at
                ]);
                const csvContent = [headers, ...rows]
                    .map(row => row.map(cell => `"${cell}"`).join(';'))
                    .join('\\n');

                // Добавляем BOM для корректного отображения кириллицы в Excel
                const blob = new Blob(['\\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                const now = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-');
                link.href = url;
                link.download = `sensors_${now}.csv`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                URL.revokeObjectURL(url);
            }

            // Загрузка общего количества записей
            async function loadTotalCount() {
                try {
                    const resp = await fetch('/api/v1/sensors/all?limit=10000');
                    const data = await resp.json();
                    document.getElementById('totalCount').textContent = data.length;
                } catch (e) {
                    console.error(e);
                }
            }

            // Инициализация
            document.addEventListener('DOMContentLoaded', () => {
                initCharts();
                loadLatest();
                loadData();
                loadTotalCount();

                // Автообновление каждые 30 секунд
                setInterval(() => {
                    loadLatest();
                    loadData();
                    loadTotalCount();
                }, 30000);
            });
        </script>
    </body>
    </html>
    """
    return html
