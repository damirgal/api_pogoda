# Документация API для передачи данных датчиков (Sensor Data API)

## 📋 Описание

REST API для приёма и хранения показаний датчиков температуры, влажности и давления в базе данных SQLite. API защищён токеном для предотвращения несанкционированного доступа.

---

## 🚀 Быстрый старт

### Установка зависимостей
```bash
pip install fastapi uvicorn pydantic
```

### Запуск сервера
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

После запуска API доступен по адресу: `http://localhost:8000`

### Интерактивная документация
FastAPI автоматически генерирует интерактивную документацию:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🔐 Аутентификация

Все запросы к API должны содержать заголовок `X-API-Token` с валидным токеном.

| Параметр | Расположение | Описание |
|----------|--------------|----------|
| `X-API-Token` | HTTP Header | Секретный токен для авторизации |

**Пример заголовка:**
```
X-API-Token: my_super_secret_token_2026
```

> ⚠️ **Важно:** При запросах без токена или с неверным токеном сервер вернёт ошибку `401 Unauthorized`.

---

## 📡 Endpoints

### 1. Отправка показаний датчиков

Принимает данные с датчиков и сохраняет их в базу данных.

| Параметр | Значение |
|----------|----------|
| **URL** | `/api/v1/sensors` |
| **Метод** | `POST` |
| **Content-Type** | `application/json` |
| **Аутентификация** | Требуется (`X-API-Token`) |

#### Тело запроса (JSON)

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `temperature` | `float` | ✅ | Температура |
| `humidity` | `float` | ✅ | Влажность |
| `pressure` | `float` | ✅ | Давление |
| `recorded_at` | `string` | ✅ | Дата и время в формате ISO 8601 |

**Формат даты:** `YYYY-MM-DDTHH:MM:SS` (например, `2026-07-04T14:30:00`)

#### Пример запроса (curl)
```bash
curl -X POST "http://localhost:8000/api/v1/sensors" \
     -H "X-API-Token: my_super_secret_token_2026" \
     -H "Content-Type: application/json" \
     -d '{
           "temperature": 24.5,
           "humidity": 48.2,
           "pressure": 1013.1,
           "recorded_at": "2026-07-04T14:30:00"
         }'
```

#### Пример запроса (Python)
```python
import requests

url = "http://localhost:8000/api/v1/sensors"
headers = {
    "X-API-Token": "my_super_secret_token_2026",
    "Content-Type": "application/json"
}
data = {
    "temperature": 24.5,
    "humidity": 48.2,
    "pressure": 1013.1,
    "recorded_at": "2026-07-04T14:30:00"
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

#### Пример запроса (ESP32 / Arduino с HTTPClient)
```cpp
#include <HTTPClient.h>

HTTPClient http;
http.begin("http://YOUR_SERVER_IP:8000/api/v1/sensors");
http.addHeader("Content-Type", "application/json");
http.addHeader("X-API-Token", "my_super_secret_token_2026");

String payload = "{\"temperature\":24.5,\"humidity\":48.2,\"pressure\":1013.1,\"recorded_at\":\"2026-07-04T14:30:00\"}";
int httpCode = http.POST(payload);
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

Возвращает последнюю запись из базы данных.

| Параметр | Значение |
|----------|----------|
| **URL** | `/api/v1/sensors/latest` |
| **Метод** | `GET` |
| **Аутентификация** | Требуется (`X-API-Token`) |

#### Пример запроса
```bash
curl -X GET "http://localhost:8000/api/v1/sensors/latest" \
     -H "X-API-Token: my_super_secret_token_2026"
```

#### Успешный ответ (200 OK)
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

## 🗄️ Структура базы данных

**Файл БД:** `iot_data.db` (создаётся автоматически)  
**Таблица:** `sensor_readings`

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | `INTEGER PRIMARY KEY` | Первичный ключ (автоинкремент) |
| `temperature` | `REAL` | Температура |
| `humidity` | `REAL` | Влажность |
| `pressure` | `REAL` | Давление |
| `recorded_at` | `TEXT` | Дата и время записи (ISO 8601) |

---

## ⚠️ Коды ответов и ошибки

| Код | Описание | Когда возникает |
|-----|----------|-----------------|
| `200` | OK | Успешный GET запрос |
| `201` | Created | Данные успешно сохранены |
| `400` | Bad Request | Неверный формат даты |
| `401` | Unauthorized | Отсутствует или неверный токен |
| `404` | Not Found | В базе нет данных (для `/latest`) |
| `422` | Unprocessable Entity | Неверный формат JSON или отсутствуют обязательные поля |
| `500` | Internal Server Error | Внутренняя ошибка сервера |

#### Пример ответа с ошибкой 401 (нет токена)
```json
{
  "detail": "Неверный или отсутствующий токен доступа"
}
```

#### Пример ответа с ошибкой 422 (неверный формат)
```json
{
  "detail": [
    {
      "loc": ["body", "recorded_at"],
      "msg": "Неверный формат даты. Используйте ISO 8601 (YYYY-MM-DDTHH:MM:SS)",
      "type": "value_error"
    }
  ]
}
```

---

## 🔧 Конфигурация

Основные параметры настраиваются в файле `main.py`:

```python
SECRET_TOKEN = "my_super_secret_token_2026"  # Ваш секретный токен
DB_NAME = "iot_data.db"                      # Имя файла базы данных
```

### Рекомендации по безопасности

1. **Храните токен в переменных окружения**, а не в коде:
   ```bash
   export SENSOR_API_TOKEN="my_super_secret_token_2026"
   ```

2. **Используйте HTTPS** при передаче данных через интернет (настройте Nginx reverse proxy с Let's Encrypt).

3. **Ограничьте доступ** к порту 8000 с помощью firewall, если API работает в локальной сети.

---

## 📝 Лицензия

Свободное использование. Без гарантий.

---

## 📞 Поддержка

При возникновении вопросов или ошибок, проверьте:
1. Корректность токена в заголовке `X-API-Token`
2. Формат даты: `YYYY-MM-DDTHH:MM:SS`
3. Все ли обязательные поля присутствуют в JSON
4. Логи сервера в терминале для детальной диагностики