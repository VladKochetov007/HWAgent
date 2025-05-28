# HWAgent REST API Documentation

Новый REST API для HWAgent с полной поддержкой стриминга через WebSocket и HTTP endpoints.

## Особенности

✨ **Полная поддержка стриминга** - WebSocket и Server-Sent Events
🔄 **Управление сессиями** - Изолированные контексты для каждого пользователя  
🛠️ **Все инструменты** - Полная поддержка всех инструментов HWAgent
🎨 **Современный UI** - Красивый и отзывчивый веб-интерфейс
📡 **REST API** - Полноценный REST API для интеграции
🌐 **CORS поддержка** - Готов для использования с внешними фронтендами

## Быстрый старт

### 1. Установите зависимости
```bash
pip install -r requirements.txt
```

### 2. Настройте переменные окружения
```bash
export OPENROUTER_API_KEY="your_api_key_here"
```

### 3. Запустите сервер
```bash
python run_api_server.py
```

### 4. Откройте веб-интерфейс
Перейдите на http://127.0.0.1:5000

## API Endpoints

### Управление сессиями

#### Создание сессии
```http
POST /api/sessions
```

**Ответ:**
```json
{
  "session_id": "uuid-string",
  "created_at": "2024-01-01T12:00:00Z",
  "tools_available": 6
}
```

#### Получение информации о сессии
```http
GET /api/sessions/{session_id}
```

#### Удаление сессии
```http
DELETE /api/sessions/{session_id}
```

### Отправка сообщений

#### Стандартный режим (без стриминга)
```http
POST /api/sessions/{session_id}/messages
Content-Type: application/json

{
  "message": "Ваше сообщение"
}
```

**Ответ:**
```json
{
  "response": "Ответ агента",
  "timestamp": "2024-01-01T12:00:00Z",
  "session_id": "uuid-string"
}
```

#### Потоковый режим (Server-Sent Events)
```http
POST /api/sessions/{session_id}/stream
Content-Type: application/json

{
  "message": "Ваше сообщение"
}
```

**Потоковый ответ:**
```
data: {"type": "start", "message": "Processing..."}

data: {"type": "complete", "response": "Полный ответ"}
```

### Управление контекстом

#### Получение контекста
```http
GET /api/sessions/{session_id}/context
```

#### Очистка контекста
```http
DELETE /api/sessions/{session_id}/context
```

### Информация о системе

#### Health Check
```http
GET /api/health
```

**Ответ:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "active_sessions": 3
}
```

#### Список доступных инструментов
```http
GET /api/tools
```

**Ответ:**
```json
{
  "tools": [
    {
      "name": "create_file",
      "description": "Create files with content",
      "parameters": {...}
    }
  ],
  "count": 6
}
```

## WebSocket API

### Подключение
```javascript
const socket = io('http://127.0.0.1:5000');
```

### События

#### Отправка сообщения
```javascript
socket.emit('send_message', {
  message: 'Ваше сообщение'
});
```

#### Получение ответов
```javascript
// Начало обработки
socket.on('stream_start', (data) => {
  console.log('Обработка началась:', data.message);
});

// Части ответа (стриминг)
socket.on('stream_chunk', (data) => {
  if (data.type === 'content') {
    console.log('Новая часть:', data.content);
  }
});

// Завершение обработки
socket.on('stream_complete', (data) => {
  console.log('Полный ответ:', data.response);
});

// Ошибки
socket.on('error', (data) => {
  console.error('Ошибка:', data.message);
});
```

#### Управление контекстом
```javascript
// Очистка контекста
socket.emit('clear_context');

// Получение контекста
socket.emit('get_context');

socket.on('context_cleared', (data) => {
  console.log('Контекст очищен');
});

socket.on('context_summary', (data) => {
  console.log('Контекст:', data.summary);
});
```

## Веб-интерфейс

Современный веб-интерфейс доступен по адресу: http://127.0.0.1:5000

### Возможности интерфейса:

- 💬 **Чат с агентом** - Стриминговый и обычный режимы
- ⚙️ **Настройки** - Переключение режимов стриминга
- 🛠️ **Инструменты** - Просмотр доступных инструментов
- 📊 **Информация о сессии** - ID сессии, количество сообщений
- 🗑️ **Управление контекстом** - Очистка истории
- 💾 **Экспорт чата** - Сохранение истории в JSON
- 📱 **Адаптивный дизайн** - Работает на мобильных устройствах

### Горячие клавиши:
- `Ctrl + Enter` - Отправить сообщение
- `Shift + Enter` - Новая строка в тексте

## Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `OPENROUTER_API_KEY` | API ключ OpenRouter | *Обязательно* |
| `HOST` | Хост сервера | `127.0.0.1` |
| `PORT` | Порт сервера | `5000` |
| `DEBUG` | Режим отладки | `False` |
| `SECRET_KEY` | Секретный ключ Flask | `hwagent-secret-key-2024` |

### Пример .env файла
```bash
OPENROUTER_API_KEY=your_api_key_here
HOST=0.0.0.0
PORT=8080
DEBUG=true
SECRET_KEY=your_secret_key_here
```

## Архитектура

### Компоненты системы:

1. **API Server** (`hwagent/api_server.py`)
   - Flask + Flask-SocketIO
   - REST endpoints
   - WebSocket handlers
   - Управление сессиями

2. **Streaming Agent** (`StreamingReActAgent`)
   - Расширенный ReActAgent
   - WebSocket эмиссия событий
   - Потоковая обработка

3. **Frontend** (`static/`)
   - Современный JS/CSS
   - WebSocket клиент
   - Управление UI состоянием

### Поток данных:

```
User Input → WebSocket/HTTP → API Server → Agent → Tools → Response → User
```

## Примеры использования

### Python клиент
```python
import requests
import json

# Создание сессии
response = requests.post('http://127.0.0.1:5000/api/sessions')
session_data = response.json()
session_id = session_data['session_id']

# Отправка сообщения
message_data = {'message': 'Вычисли сумму от 1 до 100'}
response = requests.post(
    f'http://127.0.0.1:5000/api/sessions/{session_id}/messages',
    json=message_data
)
result = response.json()
print(result['response'])
```

### JavaScript клиент
```javascript
// Создание сессии
const response = await fetch('/api/sessions', {
  method: 'POST'
});
const session = await response.json();

// Отправка сообщения
const messageResponse = await fetch(`/api/sessions/${session.session_id}/messages`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({message: 'Привет!'})
});
const result = await messageResponse.json();
console.log(result.response);
```

## Сравнение с оригинальным сервером

| Функция | Оригинальный | Новый API |
|---------|--------------|-----------|
| WebSocket стриминг | ✅ | ✅ |
| REST API | ❌ | ✅ |
| Управление сессиями | ❌ | ✅ |
| Server-Sent Events | ❌ | ✅ |
| Современный UI | ⚠️ | ✅ |
| API документация | ❌ | ✅ |
| Обработка ошибок | ⚠️ | ✅ |
| CORS поддержка | ✅ | ✅ |

## Troubleshooting

### Проблемы с подключением
1. Проверьте, что сервер запущен
2. Убедитесь, что порт не занят
3. Проверьте настройки CORS

### WebSocket не работает
1. Убедитесь, что порт доступен
2. Проверьте настройки прокси/firewall
3. Попробуйте режим polling

### Ошибки API
1. Проверьте правильность API ключа
2. Убедитесь в корректности JSON запросов
3. Проверьте логи сервера

## Дальнейшее развитие

### Планируемые функции:
- 🔐 Аутентификация пользователей
- 💾 Постоянное хранение сессий
- 📈 Метрики и аналитика
- 🔧 Управление инструментами через API
- 📄 Загрузка файлов
- 🌍 Интернационализация

### Интеграция:
- Kubernetes deployment
- Docker контейнеры
- CI/CD pipelines
- Мониторинг и логирование 