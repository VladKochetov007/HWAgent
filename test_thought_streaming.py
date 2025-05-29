#!/usr/bin/env python3
"""
Тестовый скрипт для демонстрации потоковых мыслей агента через WebSocket
"""

import socketio
import asyncio
import time
import json

class ThoughtStreamingDemo:
    def __init__(self):
        self.sio = socketio.AsyncClient()
        self.session_id = None
        self.setup_event_handlers()
        
    def setup_event_handlers(self):
        @self.sio.event
        async def connect():
            print("🔗 Подключен к серверу")
            
        @self.sio.event
        async def disconnect():
            print("❌ Отключен от сервера")
            
        @self.sio.event
        async def session_joined(data):
            print(f"✅ Присоединился к сессии: {data['session_id']}")
            
        @self.sio.event
        async def thought_stream(data):
            print(f"💭 Поток мыслей: {data['type']} - {data['content'][:100]}...")
            
        @self.sio.event
        async def stream_start(data):
            print("🚀 Начало потока ответа")
            
        @self.sio.event
        async def stream_data(data):
            print(f"📝 Данные потока: {data.get('content', '')[:50]}...")
            
        @self.sio.event
        async def stream_complete(data):
            print("✅ Поток завершен")
            
    async def connect_and_test(self):
        try:
            # Подключение к серверу
            await self.sio.connect('http://localhost:5000')
            
            # Создание сессии
            response = await self.create_session()
            if not response:
                return
                
            self.session_id = response['session_id']
            print(f"📋 Создана сессия: {self.session_id}")
            
            # Присоединение к сессии
            await self.sio.emit('join_session', {'session_id': self.session_id})
            await asyncio.sleep(1)
            
            # Отправка тестового сообщения
            test_message = "Создай файл с кодом Python для решения квадратного уравнения и объясни каждый шаг"
            print(f"📤 Отправка сообщения: {test_message}")
            
            await self.sio.emit('send_message', {
                'session_id': self.session_id,
                'message': test_message,
                'streaming': True
            })
            
            # Ожидание ответа
            print("⏳ Ожидание ответа агента...")
            await asyncio.sleep(30)  # Ждем 30 секунд для демонстрации
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        finally:
            await self.sio.disconnect()
            
    async def create_session(self):
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post('http://localhost:5000/api/sessions') as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    print(f"❌ Ошибка создания сессии: {resp.status}")
                    return None

async def main():
    print("🧠 Демонстрация потоковых мыслей HWAgent")
    print("=" * 50)
    
    demo = ThoughtStreamingDemo()
    await demo.connect_and_test()

if __name__ == "__main__":
    asyncio.run(main()) 