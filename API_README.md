# HWAgent REST API Documentation

New REST API for HWAgent with full streaming support via WebSocket and HTTP endpoints.

## Features

✨ **Full Streaming Support** - WebSocket and Server-Sent Events
🔄 **Session Management** - Isolated contexts for each user
🛠️ **All Tools** - Full support for all HWAgent tools
🎨 **Modern UI** - Beautiful and responsive web interface
📡 **REST API** - Full-fledged REST API for integration
🌐 **CORS Support** - Ready for use with external frontends

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
```bash
export OPENROUTER_API_KEY="your_api_key_here"
```

### 3. Run the Server
```bash
python run_api_server.py
```

### 4. Open Web Interface
Navigate to http://127.0.0.1:5000

## API Endpoints

### Session Management

#### Create Session
```http
POST /api/sessions
```

**Response:**
```json
{
  "session_id": "uuid-string",
  "created_at": "2024-01-01T12:00:00Z",
  "tools_available": 6
}
```

#### Get Session Information
```http
GET /api/sessions/{session_id}
```

#### Delete Session
```http
DELETE /api/sessions/{session_id}
```

### Sending Messages

#### Standard Mode (Non-Streaming)
```http
POST /api/sessions/{session_id}/messages
Content-Type: application/json

{
  "message": "Your message"
}
```

**Response:**
```json
{
  "response": "Agent's response",
  "timestamp": "2024-01-01T12:00:00Z",
  "session_id": "uuid-string"
}
```

#### Streaming Mode (Server-Sent Events)
```http
POST /api/sessions/{session_id}/stream
Content-Type: application/json

{
  "message": "Your message"
}
```

**Streamed Response:**
```
data: {"type": "start", "message": "Processing..."}

data: {"type": "complete", "response": "Full response"}
```

### Context Management

#### Get Context
```http
GET /api/sessions/{session_id}/context
```

#### Clear Context
```http
DELETE /api/sessions/{session_id}/context
```

### System Information

#### Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "active_sessions": 3
}
```

#### List Available Tools
```http
GET /api/tools
```

**Response:**
```json
{
  "tools": [
    {
      "name": "create_file",
      "description": "Create files with content",
      "parameters": {}
    }
  ],
  "count": 6
}
```

## WebSocket API

### Connection
```javascript
const socket = io('http://127.0.0.1:5000');
```

### Events

#### Sending a Message
```javascript
socket.emit('send_message', {
  message: 'Your message'
});
```

#### Receiving Responses
```javascript
// Processing started
socket.on('stream_start', (data) => {
  console.log('Processing started:', data.message);
});

// Response parts (streaming)
socket.on('stream_chunk', (data) => {
  if (data.type === 'content') {
    console.log('New part:', data.content);
  }
});

// Processing completed
socket.on('stream_complete', (data) => {
  console.log('Full response:', data.response);
});

// Errors
socket.on('error', (data) => {
  console.error('Error:', data.message);
});
```

#### Context Management
```javascript
// Clear context
socket.emit('clear_context');

// Get context
socket.emit('get_context');

socket.on('context_cleared', (data) => {
  console.log('Context cleared');
});

socket.on('context_summary', (data) => {
  console.log('Context:', data.summary);
});
```

## Web Interface

A modern web interface is available at: http://127.0.0.1:5000

### Interface Features:

- 💬 **Chat with Agent** - Streaming and standard modes
- ⚙️ **Settings** - Switch streaming modes
- 🛠️ **Tools** - View available tools
- 📊 **Session Information** - Session ID, message count
- 🗑️ **Context Management** - Clear history
- 💾 **Export Chat** - Save history to JSON
- 📱 **Responsive Design** - Works on mobile devices

### Hotkeys:
- `Ctrl + Enter` - Send message
- `Shift + Enter` - New line in text

## Configuration

### Environment Variables

| Variable           | Description             | Default                       |
|--------------------|-------------------------|-------------------------------|
| `OPENROUTER_API_KEY` | OpenRouter API key      | *Required*                    |
| `HOST`               | Server host             | `127.0.0.1`                   |
| `PORT`               | Server port             | `5000`                        |
| `DEBUG`              | Debug mode              | `False`                       |
| `SECRET_KEY`         | Flask secret key        | `hwagent-secret-key-2024`     |

### Example .env file
```bash
OPENROUTER_API_KEY=your_api_key_here
HOST=0.0.0.0
PORT=8080
DEBUG=true
SECRET_KEY=your_secret_key_here
```

## Architecture

### System Components:

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