#!/usr/bin/env python3
"""
Простой тест для проверки работы HWAgent REST API.
Проверяет основные endpoint'ы и функциональность.
"""

import requests
import json
import time
import sys
from typing import Dict, Any


class APITester:
    """Простой тестер для HWAgent API."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:5000"):
        self.base_url = base_url
        self.session_id: str | None = None
        
    def test_health(self) -> bool:
        """Проверка health endpoint."""
        print("🔍 Тестирование health endpoint...")
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health OK: {data['status']}")
                return True
            else:
                print(f"❌ Health failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health error: {e}")
            return False
    
    def test_create_session(self) -> bool:
        """Создание новой сессии."""
        print("🔍 Создание новой сессии...")
        try:
            response = requests.post(f"{self.base_url}/api/sessions", timeout=10)
            if response.status_code == 201:
                data = response.json()
                self.session_id = data["session_id"]
                print(f"✅ Сессия создана: {self.session_id}")
                return True
            else:
                print(f"❌ Ошибка создания сессии: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Ошибка создания сессии: {e}")
            return False
    
    def test_session_info(self) -> bool:
        """Получение информации о сессии."""
        if not self.session_id:
            print("❌ Нет активной сессии для тестирования")
            return False
            
        print("🔍 Получение информации о сессии...")
        try:
            response = requests.get(
                f"{self.base_url}/api/sessions/{self.session_id}",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Информация о сессии получена: {data}")
                return True
            else:
                print(f"❌ Ошибка получения информации: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Ошибка получения информации: {e}")
            return False
    
    def test_send_message(self) -> bool:
        """Отправка сообщения."""
        if not self.session_id:
            print("❌ Нет активной сессии для отправки сообщения")
            return False
            
        print("🔍 Отправка тестового сообщения...")
        try:
            message_data = {
                "message": "Привет! Можешь посчитать 2 + 2?"
            }
            response = requests.post(
                f"{self.base_url}/api/sessions/{self.session_id}/messages",
                json=message_data,
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Ответ получен: {data['response'][:100]}...")
                return True
            else:
                print(f"❌ Ошибка отправки сообщения: {response.status_code}")
                if response.text:
                    print(f"Детали: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Ошибка отправки сообщения: {e}")
            return False
    
    def test_tools_endpoint(self) -> bool:
        """Проверка endpoint инструментов."""
        print("🔍 Получение списка инструментов...")
        try:
            response = requests.get(f"{self.base_url}/api/tools", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Найдено инструментов: {data['count']}")
                for tool in data['tools'][:3]:  # Показываем первые 3
                    print(f"  - {tool['name']}: {tool['description']}")
                return True
            else:
                print(f"❌ Ошибка получения инструментов: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Ошибка получения инструментов: {e}")
            return False
    
    def test_context_management(self) -> bool:
        """Тестирование управления контекстом."""
        if not self.session_id:
            print("❌ Нет активной сессии для управления контекстом")
            return False
            
        print("🔍 Тестирование управления контекстом...")
        try:
            # Получение контекста
            response = requests.get(
                f"{self.base_url}/api/sessions/{self.session_id}/context",
                timeout=5
            )
            if response.status_code == 200:
                print("✅ Контекст получен")
            
            # Очистка контекста
            response = requests.delete(
                f"{self.base_url}/api/sessions/{self.session_id}/context",
                timeout=5
            )
            if response.status_code == 200:
                print("✅ Контекст очищен")
                return True
            else:
                print(f"❌ Ошибка очистки контекста: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка управления контекстом: {e}")
            return False
    
    def test_delete_session(self) -> bool:
        """Удаление сессии."""
        if not self.session_id:
            print("❌ Нет активной сессии для удаления")
            return False
            
        print("🔍 Удаление сессии...")
        try:
            response = requests.delete(
                f"{self.base_url}/api/sessions/{self.session_id}",
                timeout=5
            )
            if response.status_code == 200:
                print("✅ Сессия удалена")
                self.session_id = None
                return True
            else:
                print(f"❌ Ошибка удаления сессии: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Ошибка удаления сессии: {e}")
            return False
    
    def run_all_tests(self) -> None:
        """Запуск всех тестов."""
        print("🚀 Запуск тестов HWAgent REST API\n")
        print(f"Тестируем сервер: {self.base_url}")
        print("=" * 50)
        
        tests = [
            ("Health Check", self.test_health),
            ("Создание сессии", self.test_create_session),
            ("Информация о сессии", self.test_session_info),
            ("Список инструментов", self.test_tools_endpoint),
            ("Отправка сообщения", self.test_send_message),
            ("Управление контекстом", self.test_context_management),
            ("Удаление сессии", self.test_delete_session),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n{test_name}:")
            try:
                if test_func():
                    passed += 1
                time.sleep(1)  # Небольшая пауза между тестами
            except KeyboardInterrupt:
                print("\n❌ Тестирование прервано пользователем")
                break
            except Exception as e:
                print(f"❌ Неожиданная ошибка в тесте '{test_name}': {e}")
        
        print("\n" + "=" * 50)
        print(f"📊 Результаты: {passed}/{total} тестов прошли успешно")
        
        if passed == total:
            print("🎉 Все тесты прошли успешно!")
        elif passed > total // 2:
            print("⚠️ Большинство тестов прошли, но есть проблемы")
        else:
            print("❌ Много тестов не прошли, проверьте сервер")


def main():
    """Главная функция."""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://127.0.0.1:5000"
    
    print(f"HWAgent API Tester")
    print(f"Сервер: {base_url}")
    
    tester = APITester(base_url)
    tester.run_all_tests()


if __name__ == "__main__":
    main() 