"""
Консольный клиент SHIFT Messenger
Для использования в терминале без GUI
"""

import asyncio
import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.client import ShiftClient


class ConsoleClient:
    """Консольный клиент мессенджера"""
    
    def __init__(self):
        self.client = ShiftClient()
        self.username = None
        self.current_chat = None
        self.loop = asyncio.get_event_loop()
    
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
        print("\n--- Пользователи онлайн ---")
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
        return await self.loop.run_in_executor(None, input, prompt)
    
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
        timestamp = data.get('timestamp', '')[:19]
        
        if sender == self.current_chat:
            print(f"\n[{timestamp}] {sender}: {content}")
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
            timestamp = msg.get('timestamp', '')[:19]
            
            prefix = "Вы" if sender == self.username else sender
            print(f"[{timestamp}] {prefix}: {content}")
        print("--- Конец истории ---\n")
    
    def handle_users_list(self, data):
        """Обработка списка пользователей"""
        users = data.get('users', [])
        if not users:
            print("Нет пользователей онлайн")
            return
        
        print(f"Пользователи онлайн ({len(users)}):")
        for i, user in enumerate(users, 1):
            if user != self.username:
                print(f"  {i}. {user}")
    
    async def run(self):
        """Главный цикл"""
        if not await self.connect():
            return
        
        self.setup_handlers()
        
        # Главное меню
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
        
        # Основной цикл после входа
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


def main():
    """Запуск консольного клиента"""
    client = ConsoleClient()
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        print("\n\nПрерывание...")
        asyncio.run(client.client.disconnect())
    except Exception as e:
        print(f"\nОшибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()