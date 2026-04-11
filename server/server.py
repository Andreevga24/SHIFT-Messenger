"""
SHIFT Messenger Server
WebSocket сервер для обработки сообщений в реальном времени
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime
from typing import Dict, Set
import sqlite3
import os

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация
HOST = 'localhost'
PORT = 8765
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'shift.db')


class ShiftServer:
    """Класс сервера мессенджера SHIFT"""
    
    def __init__(self):
        self.connected_clients: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.user_rooms: Dict[str, Set[str]] = {}  # username -> set of room_ids
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица сообщений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                receiver TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT 0
            )
        ''')
        
        # Таблица комнат (групповых чатов)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_by TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица участников комнат
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS room_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES rooms(id),
                UNIQUE(room_id, username)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("База данных инициализирована")
    
    async def register_user(self, username: str, password: str) -> dict:
        """Регистрация нового пользователя"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO users (username, password) VALUES (?, ?)',
                (username, password)
            )
            conn.commit()
            conn.close()
            logger.info(f"Пользователь {username} зарегистрирован")
            return {"success": True, "message": "Пользователь успешно зарегистрирован"}
        except sqlite3.IntegrityError:
            return {"success": False, "message": "Пользователь уже существует"}
        except Exception as e:
            logger.error(f"Ошибка регистрации: {e}")
            return {"success": False, "message": str(e)}
    
    async def authenticate_user(self, username: str, password: str) -> dict:
        """Аутентификация пользователя"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                'SELECT id FROM users WHERE username = ? AND password = ?',
                (username, password)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {"success": True, "message": "Аутентификация успешна"}
            else:
                return {"success": False, "message": "Неверный логин или пароль"}
        except Exception as e:
            logger.error(f"Ошибка аутентификации: {e}")
            return {"success": False, "message": str(e)}
    
    async def save_message(self, sender: str, receiver: str, content: str) -> int:
        """Сохранение сообщения в базу данных"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO messages (sender, receiver, content) VALUES (?, ?, ?)',
                (sender, receiver, content)
            )
            message_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return message_id
        except Exception as e:
            logger.error(f"Ошибка сохранения сообщения: {e}")
            return -1
    
    async def get_message_history(self, user1: str, user2: str, limit: int = 50) -> list:
        """Получение истории сообщений между двумя пользователями"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT sender, receiver, content, timestamp, is_read
                FROM messages
                WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user1, user2, user2, user1, limit))
            messages = cursor.fetchall()
            conn.close()
            return [
                {
                    "sender": msg[0],
                    "receiver": msg[1],
                    "content": msg[2],
                    "timestamp": msg[3],
                    "is_read": bool(msg[4])
                }
                for msg in messages
            ]
        except Exception as e:
            logger.error(f"Ошибка получения истории: {e}")
            return []
    
    async def broadcast_to_user(self, username: str, message: dict):
        """Отправка сообщения конкретному пользователю"""
        if username in self.connected_clients:
            try:
                await self.connected_clients[username].send(json.dumps(message))
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения {username}: {e}")
    
    async def handle_client(self, websocket: websockets.WebSocketServerProtocol):
        """Обработка подключения клиента"""
        username = None
        
        try:
            # Ожидание аутентификации
            auth_message = await websocket.recv()
            auth_data = json.loads(auth_message)
            
            if auth_data.get('type') == 'auth':
                username = auth_data.get('username')
                password = auth_data.get('password')
                
                if not username or not password:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Не указаны логин или пароль"
                    }))
                    return
                
                # Проверка аутентификации
                auth_result = await self.authenticate_user(username, password)
                if not auth_result['success']:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": auth_result['message']
                    }))
                    return
                
                # Регистрация подключения
                self.connected_clients[username] = websocket
                logger.info(f"Пользователь {username} подключился")
                
                await websocket.send(json.dumps({
                    "type": "connected",
                    "message": "Подключение к серверу SHIFT установлено",
                    "username": username
                }))
                
                # Обработка сообщений
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        await process_message(self, username, data)
                    except json.JSONDecodeError:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": "Неверный формат JSON"
                        }))
                    except Exception as e:
                        logger.error(f"Ошибка обработки сообщения: {e}")
            
            elif auth_data.get('type') == 'register':
                username = auth_data.get('username')
                password = auth_data.get('password')
                
                register_result = await self.register_user(username, password)
                await websocket.send(json.dumps(register_result))
                return
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Соединение с клиентом закрыто")
        except Exception as e:
            logger.error(f"Ошибка обработки клиента: {e}")
        finally:
            # Удаление клиента при отключении
            if username and username in self.connected_clients:
                del self.connected_clients[username]
                logger.info(f"Пользователь {username} отключился")


async def process_message(server: ShiftServer, sender: str, data: dict):
    """Обработка входящих сообщений от клиента"""
    message_type = data.get('type')
    
    if message_type == 'message':
        # Отправка личного сообщения
        receiver = data.get('receiver')
        content = data.get('content')
        
        if not receiver or not content:
            return
        
        # Сохранение в базу
        message_id = await server.save_message(sender, receiver, content)
        
        # Отправка получателю
        await server.broadcast_to_user(receiver, {
            "type": "message",
            "id": message_id,
            "sender": sender,
            "receiver": receiver,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Подтверждение отправителю
        await server.broadcast_to_user(sender, {
            "type": "message_sent",
            "id": message_id,
            "receiver": receiver,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    elif message_type == 'get_history':
        # Запрос истории сообщений
        other_user = data.get('user')
        if other_user:
            history = await server.get_message_history(sender, other_user)
            await server.broadcast_to_user(sender, {
                "type": "history",
                "user": other_user,
                "messages": history
            })
    
    elif message_type == 'get_users':
        # Запрос списка онлайн пользователей
        await server.broadcast_to_user(sender, {
            "type": "users_list",
            "users": list(server.connected_clients.keys())
        })


async def main():
    """Запуск сервера"""
    server = ShiftServer()
    logger.info(f"Запуск сервера SHIFT на {HOST}:{PORT}")
    
    async with websockets.serve(server.handle_client, HOST, PORT):
        logger.info("Сервер запущен и ожидает подключений...")
        await asyncio.Future()  # Бесконечное выполнение


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Сервер остановлен")