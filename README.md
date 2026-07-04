# 📚 Sensor Data API — Полная документация

REST API для приёма, хранения и визуализации показаний датчиков температуры, влажности и давления. Включает веб-интерфейс с графиками, фильтрацией и экспортом данных.

---

## 📑 Содержание

1. [Возможности](#-возможности)
2. [Требования](#-требования)
3. [Установка](#-установка)
4. [Структура проекта](#-структура-проекта)
5. [Запуск сервера](#-запуск-сервера)
6. [Веб-интерфейс](#-веб-интерфейс)
7. [API Reference](#-api-reference)
8. [Структура базы данных](#-структура-базы-данных)
9. [Безопасность](#-безопасность)
10. [Устранение неполадок](#-устранение-неполадок)

---

## ✨ Возможности

- 🔐 **Защищённый приём данных** по токену
- 📊 **Веб-дашборд** с карточками последних показаний
- 📈 **Графики** температуры, влажности и давления (Chart.js)
- 🔍 **Фильтрация** по диапазону дат
- 📥 **Экспорт в CSV** с поддержкой кириллицы
- 🔄 **Автообновление** каждые 30 секунд
- 📱 **Адаптивный дизайн** (работает на телефонах)
- 🗄️ **База данных SQLite** (не требует установки)

---

## 📋 Требования

| Компонент | Версия |
|-----------|--------|
| Python | 3.8+ |
| ОС | Linux / Windows / macOS |
| Свободное место | ~50 МБ |

---

## 🛠️ Установка

### 1. Клонируйте/скопируйте проект в папку
```bash
mkdir sensor-api && cd sensor-api
```

### 2. Создайте виртуальное окружение (рекомендуется)
```bash
python3 -m venv venv
source venv/bin/activate      # Linux/macOS
# venv\Scripts\activate       # Windows
```

### 3. Установите зависимости
```bash
pip install fastapi uvicorn pydantic
```

### 4. Создайте файл `main.py`
Скопируйте в него код из раздела [Полный код приложения](#полный-код-приложения).

---

## 📁 Структура проекта

```
sensor-api/
├── main.py              # Основной код приложения
└── iot_data.db          # База данных (создаётся автоматически)
```

---

## 🚀 Запуск сервера

### Обычный запуск (с выводом в консоль)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Параметры:**
- `--host 0.0.0.0` — принимать подключения со всех интерфейсов (для доступа с других устройств)
- `--port 8000` — порт сервера
- `--reload` — автоперезагрузка при изменении кода (для разработки)

После запуска:
- 🌐 Веб-интерфейс: `http://localhost:8000`
- 📘 Swagger UI: `http://localhost:8000/docs`
- 📗 ReDoc: `http://localhost:8000/redoc`

---

### 🐧 Запуск в фоновом режиме (Linux)

#### Способ 1: `nohup` (самый простой)
```bash
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &
```

**Управление:**
```bash
tail -f api.log              # Посмотреть логи
ps aux | grep uvicorn        # Найти PID
kill <PID>                   # Остановить
```

#### Способ 2: `screen` (с возможностью вернуться)
```bash
screen -S sensor_api                              # Создать сессию
uvicorn main:app --host 0.0.0.0 --port 8000       # Запустить сервер
# Ctrl+A, затем D                                 # Отключиться (сервер продолжит работать)
screen -r sensor_api                              # Вернуться к сессии
```

#### Способ 3: `tmux` (альтернатива screen)
```bash
tmux new -s sensor_api
uvicorn main:app --host 0.0.0.0 --port 8000
# Ctrl+B, затем D                                 # Отключиться
tmux attach -t sensor_api                         # Вернуться
```

#### Способ 4: `systemd` (продакшен, автозапуск при загрузке)

Создайте файл сервиса:
```bash
sudo nano /etc/systemd/system/sensor-api.service
```

Содержимое:
```ini
[Unit]
Description=Sensor Data API
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/sensor-api
ExecStart=/path/to/sensor-api/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

⚠️ **Замените:**
- `your_username` — ваше имя пользователя
- `/path/to/sensor-api` — путь к папке проекта

**Управление сервисом:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable sensor-api     # Автозапуск при загрузке
sudo systemctl start sensor-api      # Запустить
sudo systemctl status sensor-api     # Статус
sudo systemctl stop sensor-api       # Остановить
sudo systemctl restart sensor-api    # Перезапустить
sudo journalctl -u sensor-api -f     # Логи
```

---

### 🪟 Запуск в фоновом режиме (Windows)

#### Способ 1: `Start-Process` (PowerShell)
```powershell
Start-Process -FilePath "python" -ArgumentList "-m uvicorn main:app --host 0.0.0.0 --port 8000" -WindowStyle Hidden
```

**Остановка:**
```powershell
Stop-Process -Name python -Force
```

#### Способ 2: `pythonw.exe` (без консольного окна)

1. Создайте файл `run_server.py`:
```python
import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")
```

2. Запустите:
```powershell
Start-Process -FilePath "pythonw" -ArgumentList "run_server.py" -WindowStyle Hidden
```

---

## 🌐 Веб-интерфейс

Откройте в браузере: **`http://localhost:8000`** (или IP сервера)

### Функции дашборда

| Компонент | Описание |
|-----------|----------|
| 🎴 **Карточки** | Последние показания температуры, влажности, давления |
| 📈 **Графики** | Три отдельных графика с историей (Chart.js) |
| 🔍 **Фильтры** | Выбор диапазона дат (с точностью до минуты) |
| 📥 **Экспорт CSV** | Выгрузка отфильтрованных данных в CSV (совместим с Excel) |
| 📋 **Таблица** | История всех записей, отсортированная по дате (новые сверху) |
| 🔄 **Автообновление** | Каждые 30 секунд |

### Использование фильтров

1. Выберите **«С даты»** и/или **«По дату»**
2. Нажмите **«Применить»**
3. Графики и таблица обновятся
4. Нажмите **«Экспорт CSV»** для скачивания

> 💡 При фильтрации показываются **все** записи в диапазоне (лимит отключается).

---

## 📡 API Reference

### 🔐 Аутентификация

Все защищённые endpoints требуют заголовок:
```
X-API-Token: my_super_secret_token_2026
```

---

### 1. Отправка показаний датчиков

| Параметр | Значение |
|----------|----------|
| **URL** | `/api/v1/sensors` |
| **Метод** | `POST` |
| **Content-Type** | `application/json` |
| **Аутентификация** | ✅ Требуется |

#### Тело запроса

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `temperature` | `float` | ✅ | Температура |
| `humidity` | `float` | ✅ | Влажность |
| `pressure` | `float` | ✅ | Давление |
| `recorded_at` | `string` | ✅ | Дата/время в ISO 8601 (`YYYY-MM-DDTHH:MM:SS`) |

#### Пример (curl)
```bash
curl -X POST "http://localhost:8000/api/v1/sensors" \
     -H "X-API-Token: my_super_secret_token_2026" \
     -H "Content-Type: application/json" \
     -d "{\"temperature\": 24.5, \"humidity\": 48.2, \"pressure\": 1013.1, \"recorded_at\": \"2026-07-04T14:30:00\"}"
```

#### Пример (Python)
```python
import requests

url = "http://localhost:8000/api/v1/sensors"
headers = {"X-API-Token": "my_super_secret_token_2026"}
data = {
    "temperature": 24.5,
    "humidity": 48.2,
    "pressure": 1013.1,
    "recorded_at": "2026-07-04T14:30:00"
}
response = requests.post(url, headers=headers, json=data)
print(response.json())
```

#### Успешный ответ (201 Created)
```json
{
  "status": "success",
  "message": "Данные успешно сохранены",
  "id": 1
}
```

---

### 2. Получение последних показаний

| Параметр | Значение |
|----------|----------|
| **URL** | `/api/v1/sensors/latest` |
| **Метод** | `GET` |
| **Аутентификация** | ✅ Требуется |

#### Пример
```bash
curl -H "X-API-Token: my_super_secret_token_2026" \
     "http://localhost:8000/api/v1/sensors/latest"
```

#### Ответ (200 OK)
```json
{
  "id": 1,
  "temperature": 24.5,
  "humidity": 48.2,
  "pressure": 1013.1,
  "recorded_at": "2026-07-04T14:30:00"
}
```

---

### 3. Получение всех данных (с фильтрами)

| Параметр | Значение |
|----------|----------|
| **URL** | `/api/v1/sensors/all` |
| **Метод** | `GET` |
| **Аутентификация** | ❌ Открытый доступ |

#### Query-параметры

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `limit` | `int` | `100` | Макс. кол-во записей (1–10000) |
| `from_date` | `string` | — | Начальная дата (`YYYY-MM-DD HH:MM:SS`) |
| `to_date` | `string` | — | Конечная дата (`YYYY-MM-DD HH:MM:SS`) |

> 📌 Если указаны `from_date`/`to_date` — параметр `limit` игнорируются, возвращаются все записи в диапазоне.

#### Примеры
```bash
# Последние 100 записей
curl "http://localhost:8000/api/v1/sensors/all"

# Последние 10 записей
curl "http://localhost:8000/api/v1/sensors/all?limit=10"

# Данные за конкретный день
curl "http://localhost:8000/api/v1/sensors/all?from_date=2026-07-04 00:00:00&to_date=2026-07-04 23:59:59"
```

#### Ответ (200 OK)
```json
[
  {
    "id": 1,
    "temperature": 24.5,
    "humidity": 48.2,
    "pressure": 1013.1,
    "recorded_at": "2026-07-04T14:30:00"
  }
]
```

---

### 4. Веб-интерфейс

| Параметр | Значение |
|----------|----------|
| **URL** | `/` |
| **Метод** | `GET` |
| **Аутентификация** | ❌ Открытый доступ |

Возвращает HTML-страницу дашборда.

---

## 🗄️ Структура базы данных

**Файл:** `iot_data.db` (создаётся автоматически при первом запуске)  
**Таблица:** `sensor_readings`

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | `INTEGER PRIMARY KEY` | Первичный ключ (автоинкремент) |
| `temperature` | `REAL` | Температура |
| `humidity` | `REAL` | Влажность |
| `pressure` | `REAL` | Давление |
| `recorded_at` | `TEXT` | Дата/время (ISO 8601) |

### Работа с БД напрямую (SQLite CLI)
```bash
sqlite3 iot_data.db
```
```sql
-- Посмотреть все записи
SELECT * FROM sensor_readings ORDER BY recorded_at DESC;

-- Количество записей
SELECT COUNT(*) FROM sensor_readings;

-- Последние 10 записей
SELECT * FROM sensor_readings ORDER BY recorded_at DESC LIMIT 10;

-- Удалить все записи
DELETE FROM sensor_readings;
```

---

## 🔒 Безопасность

### Что защищено
| Endpoint | Доступ |
|----------|--------|
| `POST /api/v1/sensors` | 🔐 Только с токеном |
| `GET /api/v1/sensors/latest` | 🔐 Только с токеном |
| `GET /api/v1/sensors/all` | 🌐 Открытый |
| `GET /` (веб-интерфейс) | 🌐 Открытый |

### Рекомендации для продакшена

1. **Храните токен в переменных окружения**, а не в коде:
   ```bash
   export SENSOR_API_TOKEN="your_secret_token"
   ```

2. **Используйте HTTPS** при передаче через интернет (Nginx + Let's Encrypt):
   ```nginx
   server {
       listen 443 ssl;
       server_name sensors.example.com;
       
       ssl_certificate /etc/letsencrypt/live/sensors.example.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/sensors.example.com/privkey.pem;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **Ограничьте доступ** через firewall (UFW):
   ```bash
   sudo ufw allow 443/tcp    # HTTPS
   sudo ufw allow 22/tcp     # SSH
   sudo ufw enable
   ```

4. **Регулярно делайте бэкап** базы данных:
   ```bash
   cp iot_data.db backup_$(date +%Y%m%d).db
   ```

---

## ⚠️ Коды ответов

| Код | Описание |
|-----|----------|
| `200` | OK — успешный GET |
| `201` | Created — данные сохранены |
| `400` | Bad Request — неверный формат даты |
| `401` | Unauthorized — неверный/отсутствующий токен |
| `404` | Not Found — данных нет |
| `422` | Unprocessable Entity — ошибка валидации JSON |
| `500` | Internal Server Error |

---

## 🔧 Устранение неполадок

### Ошибка `422 Unprocessable Entity`
**Причина:** Неверный формат JSON или даты.  
**Решение:** Проверьте формат `recorded_at` — должен быть `YYYY-MM-DDTHH:MM:SS`.

### Ошибка `401 Unauthorized`
**Причина:** Неверный или отсутствующий токен.  
**Решение:** Убедитесь, что заголовок `X-API-Token` точно совпадает с `SECRET_TOKEN` в коде.

### Ошибка `AmpersandNotAllowed` (Windows PowerShell)
**Причина:** Символ `&` не работает для запуска в фоне в PowerShell.  
**Решение:** Используйте `Start-Process` или `pythonw.exe` (см. раздел [Запуск в фоне](#-запуск-в-фоновом-режиме-windows)).

### Порт 8000 занят
**Решение:**
```bash
# Найти процесс
sudo lsof -i :8000
# Остановить
kill <PID>
```
Или запустите на другом порту: `--port 8001`.

### Веб-интерфейс не открывается с другого устройства
**Решение:**
- Убедитесь, что сервер запущен с `--host 0.0.0.0`
- Проверьте firewall: `sudo ufw allow 8000/tcp`
- Используйте IP сервера, а не `localhost`

---

> 💡 **Полный код HTML/CSS/JS** веб-интерфейса находится в предыдущем сообщении — он слишком большой для включения в этот раздел. Скопируйте его из ответа выше.

</details>

---

## 📞 Поддержка

При возникновении вопросов проверьте:
1. ✅ Корректность токена в заголовке `X-API-Token`
2. ✅ Формат даты: `YYYY-MM-DDTHH:MM:SS`
3. ✅ Все обязательные поля присутствуют в JSON
4. ✅ Логи сервера в терминале / `journalctl`
5. ✅ Порт не занят другим процессом

---

**Версия:** 1.0  
**Дата:** 5 июля 2026  
**Лицензия:** Свободное использование