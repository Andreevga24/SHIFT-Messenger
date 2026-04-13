"""
Консольный клиент SHIFT Messenger
Для использования в терминале без GUI
"""

import asyncio
import sys
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.client import ShiftClient


class ConsoleClient:
    """Консольный клиент мессенджера"""
    
    def __init__(self):
        self.client = ShiftClient()
        self.username = None
        self.current_chat = None
        self.executor = ThreadPoolExecutor(max_workers=1)
    
    async def connect(self):
        """Подключение к серверу"""
        print("Подключение к серверу...")
        if await self.client.connect():
            print("✓ Подключено к серверу!")
            return True
        else:
            print("✗ Не удалось подключиться к серверу")
            return False
    
    async def register(self):
        """Регистрация пользователя"""
        print("\n--- Регистрация ---")
        username = await self.async_input("Имя пользователя: ")
        password = await self.async_input("Пароль: ")
        
        result = await self.client.register(username, password)
        if result['success']:
            print(f"✓ {result['message']}")
            return True
        else:
            print(f"✗ {result['message']}")
            return False
    
    async def login(self):
        """Вход в систему"""
        print("\n--- Вход ---")
        username = await self.async_input("Имя пользователя: ")
        password = await self.async_input("Пароль: ")
        
        result = await self.client.login(username, password)
        if result['success']:
            self.username = username
            print(f"✓ Добро пожаловать, {username}!")
            return True
        else:
            print(f"✗ {result['message']}")
            return False
    
    async def show_users(self):
        """Показать список пользователей"""
        print("\n--- Пользователи ---")
        await self.client.get_users_list()
        await asyncio.sleep(0.5)
    
    async def select_chat(self):
        """Выбрать чат"""
        user = await self.async_input("\nВведите имя пользователя для чата: ")
        if user:
            self.current_chat = user
            print(f"\n--- Чат с {user} ---")
            await self.client.get_history(user)
            await asyncio.sleep(0.5)
    
    async def send_message(self):
        """Отправить сообщение"""
        if not self.current_chat:
            print("Сначала выберите чат!")
            return
        
        content = await self.async_input("Ваше сообщение: ")
        if content:
            await self.client.send_message(self.current_chat, content)
            await asyncio.sleep(0.2)
    
    async def async_input(self, prompt: str) -> str:
        """Асинхронный ввод"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, input, prompt)
    
    def setup_handlers(self):
        """Настройка обработчиков событий"""
        self.client.on('connected', lambda data: print(f"✓ {data.get('message')}"))
        
        self.client.on('message', self.handle_message)
        self.client.on('message_sent', lambda data: print(f"✓ Сообщение отправлено {data.get('receiver')}"))
        
        self.client.on('history', self.handle_history)
        
        self.client.on('users_list', self.handle_users_list)
        
        self.client.on('error', lambda data: print(f"✗ Ошибка: {data.get('message')}"))
    
    def handle_message(self, data):
        """Обработка входящего сообщения"""
        sender = data.get('sender')
        content = data.get('content')
        timestamp = data.get('timestamp', '')
        
        # Форматирование времени
        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            formatted_time = timestamp[:19] if len(timestamp) >= 19 else timestamp
        
        if sender == self.current_chat:
            print(f"\n[{formatted_time}] {sender}: {content}")
        else:
            print(f"\n📩 Новое сообщение от {sender}: {content}")
    
    def handle_history(self, data):
        """Обработка истории сообщений"""
        messages = data.get('messages', [])
        if not messages:
            print("Нет истории сообщений")
            return
        
        print(f"\n--- История сообщений ({len(messages)} шт) ---")
        for msg in reversed(messages):
            sender = msg.get('sender')
            content = msg.get('content')
            timestamp = msg.get('timestamp', '')
            
            # Форматирование времени
            try:
                dt = datetime.fromisoformat(timestamp)
                formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                formatted_time = timestamp[:19] if len(timestamp) >= 19 else timestamp
            
            prefix = "Вы" if sender == self.username else sender
            print(f"[{formatted_time}] {prefix}: {content}")
        print("--- Конец истории ---\n")
    
    def handle_users_list(self, data):
        """Обработка списка пользователей"""
        users = data.get('users', [])
        online = set(data.get('online') or [])
        if not users:
            print("В базе нет зарегистрированных пользователей")
            return
        print(f"Зарегистрировано: {len(users)}, онлайн сейчас: {len(online)}")
        n = 0
        for user in users:
            if user == self.username:
                continue
            n += 1
            tag = " [онлайн]" if user in online else ""
            print(f"  {n}. {user}{tag}")
    
    async def run(self):
        """Главный цикл"""
        try:
            if not await self.connect():
                return

            self.setup_handlers()

            while True:
                print("\n" + "=" * 40)
                print("SHIFT Messenger - Консольный клиент")
                print("=" * 40)
                print("1. Регистрация")
                print("2. Вход")
                print("3. Показать пользователей")
                print("4. Выбрать чат")
                print("5. Отправить сообщение")
                print("0. Выход")
                print("=" * 40)

                choice = await self.async_input("\nВаш выбор: ")

                if choice == '1':
                    await self.register()
                elif choice == '2':
                    if await self.login():
                        break
                elif choice == '0':
                    print("До свидания!")
                    await self.client.disconnect()
                    return
                else:
                    print("Сначала войдите в систему!")

            while True:
                print("\n" + "=" * 40)
                print(f"Пользователь: {self.username}")
                print(f"Текущий чат: {self.current_chat or 'Не выбран'}")
                print("=" * 40)
                print("1. Показать пользователей")
                print("2. Выбрать чат")
                print("3. Отправить сообщение")
                print("4. Обновить историю чата")
                print("0. Выход")
                print("=" * 40)

                choice = await self.async_input("\nВаш выбор: ")

                if choice == '1':
                    await self.show_users()
                elif choice == '2':
                    await self.select_chat()
                elif choice == '3':
                    await self.send_message()
                elif choice == '4':
                    if self.current_chat:
                        await self.client.get_history(self.current_chat)
                        await asyncio.sleep(0.5)
                    else:
                        print("Сначала выберите чат!")
                elif choice == '0':
                    print("До свидание!")
                    await self.client.disconnect()
                    return
        finally:
            self.executor.shutdown(wait=False)
            if self.client.connected:
                await self.client.disconnect()


def main():
    """Запуск консольного клиента"""
    client = ConsoleClient()
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        print("\n\nПрерывание...")
    except Exception as e:
        print(f"\nОшибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()