"""
SHIFT Messenger Client
Клиентский модуль для подключения к серверу
"""

import asyncio
import websockets
import json
from typing import Callable, Optional
from datetime import datetime


class ShiftClient:
    """Клиент мессенджера SHIFT"""
    
    def __init__(self):
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.username: Optional[str] = None
        self.connected = False
        self.message_handlers = {
            'message': [],
            'message_sent': [],
            'history': [],
            'users_list': [],
            'connected': [],
            'error': []
        }
    
    def on(self, event_type: str, callback: Callable):
        """Регистрация обработчика событий"""
        if event_type in self.message_handlers:
            self.message_handlers[event_type].append(callback)
    
    def _emit(self, event_type: str, data: dict):
        """Вызов обработчиков событий"""
        if event_type in self.message_handlers:
            for callback in self.message_handlers[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"Ошибка в обработчике {event_type}: {e}")
    
    async def connect(self, host: str = 'localhost', port: int = 8765):
        """Подключение к серверу"""
        try:
            uri = f"ws://{host}:{port}"
            self.websocket = await websockets.connect(uri)
            self.connected = True
            print(f"Подключено к {uri}")
            
            # Запуск прослушивания сообщений
            asyncio.create_task(self._listen())
            return True
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False
    
    async def disconnect(self):
        """Отключение от сервера"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            self.username = None
            print("Отключено от сервера")
    
    async def register(self, username: str, password: str) -> dict:
        """Регистрация нового пользователя"""
        if not self.websocket:
            return {"success": False, "message": "Нет подключения к серверу"}
        
        message = {
            "type": "register",
            "username": username,
            "password": password
        }
        
        await self.websocket.send(json.dumps(message))
        
        # Ждем ответа
        response = await self.websocket.recv()
        return json.loads(response)
    
    async def login(self, username: str, password: str) -> dict:
        """Вход в систему"""
        if not self.websocket:
            return {"success": False, "message": "Нет подключения к серверу"}
        
        message = {
            "type": "auth",
            "username": username,
            "password": password
        }
        
        await self.websocket.send(json.dumps(message))
        
        # Ждем ответа
        response = await self.websocket.recv()
        data = json.loads(response)
        
        if data.get('type') == 'connected':
            self.username = username
            return {"success": True, "message": "Вход выполнен успешно"}
        elif data.get('type') == 'error':
            return {"success": False, "message": data.get('message')}
        
        return {"success": False, "message": "Неизвестный ответ сервера"}
    
    async def send_message(self, receiver: str, content: str):
        """Отправка сообщения"""
        if not self.websocket or not self.connected:
            print("Нет подключения к серверу")
            return
        
        message = {
            "type": "message",
            "receiver": receiver,
            "content": content
        }
        
        await self.websocket.send(json.dumps(message))
    
    async def get_history(self, user: str):
        """Запрос истории сообщений с пользователем"""
        if not self.websocket or not self.connected:
            print("Нет подключения к серверу")
            return
        
        message = {
            "type": "get_history",
            "user": user
        }
        
        await self.websocket.send(json.dumps(message))
    
    async def get_users_list(self):
        """Запрос списка онлайн пользователей"""
        if not self.websocket or not self.connected:
            print("Нет подключения к серверу")
            return
        
        message = {
            "type": "get_users"
        }
        
        await self.websocket.send(json.dumps(message))
    
    async def _listen(self):
        """Прослушивание входящих сообщений"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get('type')
                    self._emit(message_type, data)
                except json.JSONDecodeError:
                    print("Ошибка декодирования JSON")
                except Exception as e:
                    print(f"Ошибка обработки сообщения: {e}")
        except websockets.exceptions.ConnectionClosed:
            print("Соединение с сервером закрыто")
            self.connected = False
            self.username = None
        except Exception as e:
            print(f"Ошибка прослушивания: {e}")
            self.connected = False


# Синхронная обёртка для использования в GUI
class SyncShiftClient:
    """Синхронная обёртка для клиента"""
    
    def __init__(self):
        self.client = ShiftClient()
        self.loop = asyncio.new_event_loop()
        self._running = False
    
    def connect(self, host: str = 'localhost', port: int = 8765) -> bool:
        """Подключение к серверу"""
        try:
            result = self.loop.run_until_complete(self.client.connect(host, port))
            return result
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False
    
    def disconnect(self):
        """Отключение от сервера"""
        try:
            self.loop.run_until_complete(self.client.disconnect())
        except Exception as e:
            print(f"Ошибка отключения: {e}")
    
    def register(self, username: str, password: str) -> dict:
        """Регистрация нового пользователя"""
        try:
            return self.loop.run_until_complete(self.client.register(username, password))
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def login(self, username: str, password: str) -> dict:
        """Вход в систему"""
        try:
            return self.loop.run_until_complete(self.client.login(username, password))
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def send_message(self, receiver: str, content: str):
        """Отправка сообщения"""
        try:
            asyncio.run_coroutine_threadsafe(
                self.client.send_message(receiver, content),
                self.loop
            )
        except Exception as e:
            print(f"Ошибка отправки: {e}")
    
    def get_history(self, user: str):
        """Запрос истории сообщений"""
        try:
            asyncio.run_coroutine_threadsafe(
                self.client.get_history(user),
                self.loop
            )
        except Exception as e:
            print(f"Ошибка запроса истории: {e}")
    
    def get_users_list(self):
        """Запрос списка пользователей"""
        try:
            asyncio.run_coroutine_threadsafe(
                self.client.get_users_list(),
                self.loop
            )
        except Exception as e:
            print(f"Ошибка запроса списка: {e}")
    
    def on(self, event_type: str, callback: Callable):
        """Регистрация обработчика событий"""
        self.client.on(event_type, callback)
    
    @property
    def is_connected(self) -> bool:
        """Проверка подключения"""
        return self.client.connected
    
    @property
    def current_user(self) -> Optional[str]:
        """Текущий пользователь"""
        return self.client.username
    
    def start_event_loop(self):
        """Запуск цикла событий в отдельном потоке"""
        import threading
        self._running = True
        
        def run_loop():
            while self._running:
                self.loop.run_until_complete(asyncio.sleep(0.1))
        
        thread = threading.Thread(target=run_loop, daemon=True)
        thread.start()
    
    def stop_event_loop(self):
        """Остановка цикла событий"""
        self._running = False