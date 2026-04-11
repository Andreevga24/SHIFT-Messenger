"""
SHIFT Messenger GUI
Графический интерфейс клиента мессенджера
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTextEdit, QListWidget, QLabel,
    QDialog, QFormLayout, QMessageBox, QSplitter, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor
from datetime import datetime
from client.client import SyncShiftClient


class LoginDialog(QDialog):
    """Диалоговое окно входа/регистрации"""
    
    def __init__(self, client: SyncShiftClient):
        super().__init__()
        self.client = client
        self.username = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle('SHIFT - Вход')
        self.setFixedSize(350, 300)
        
        layout = QVBoxLayout()
        
        # Заголовок
        title = QLabel('SHIFT Messenger')
        title.setFont(QFont('Arial', 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Форма
        form_layout = QFormLayout()
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText('Введите имя пользователя')
        form_layout.addRow('Имя пользователя:', self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText('Введите пароль')
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow('Пароль:', self.password_input)
        
        layout.addLayout(form_layout)
        
        # Кнопки
        button_layout = QHBoxLayout()
        
        self.login_btn = QPushButton('Войти')
        self.login_btn.clicked.connect(self.login)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.register_btn = QPushButton('Регистрация')
        self.register_btn.clicked.connect(self.register)
        self.register_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        
        button_layout.addWidget(self.login_btn)
        button_layout.addWidget(self.register_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def login(self):
        """Вход в систему"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, 'Ошибка', 'Заполните все поля')
            return
        
        result = self.client.login(username, password)
        
        if result['success']:
            self.username = username
            self.accept()
        else:
            QMessageBox.warning(self, 'Ошибка', result['message'])
    
    def register(self):
        """Регистрация нового пользователя"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, 'Ошибка', 'Заполните все поля')
            return
        
        result = self.client.register(username, password)
        
        if result['success']:
            QMessageBox.information(self, 'Успех', 'Регистрация выполнена успешно! Теперь войдите.')
        else:
            QMessageBox.warning(self, 'Ошибка', result['message'])


class ChatMessageWidget(QWidget):
    """Виджет для отображения сообщения"""
    
    def __init__(self, sender: str, content: str, timestamp: str, is_own: bool = False):
        super().__init__()
        self.init_ui(sender, content, timestamp, is_own)
    
    def init_ui(self, sender: str, content: str, timestamp: str, is_own: bool):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Информация об отправителе и времени
        info_layout = QHBoxLayout()
        
        sender_label = QLabel(sender)
        sender_label.setFont(QFont('Arial', 10, QFont.Bold))
        
        time_label = QLabel(timestamp)
        time_label.setStyleSheet('color: gray; font-size: 10px;')
        
        if is_own:
            info_layout.addWidget(time_label)
            info_layout.addStretch()
            info_layout.addWidget(sender_label)
        else:
            info_layout.addWidget(sender_label)
            info_layout.addStretch()
            info_layout.addWidget(time_label)
        
        layout.addLayout(info_layout)
        
        # Текст сообщения
        message_label = QLabel(content)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"""
            QLabel {{
                background-color: {'#dcf8c6' if is_own else '#ffffff'};
                padding: 10px;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }}
        """)
        
        if is_own:
            message_layout = QHBoxLayout()
            message_layout.addStretch()
            message_layout.addWidget(message_label)
            message_layout.addStretch()
            layout.addLayout(message_layout)
        else:
            layout.addWidget(message_label)
        
        self.setLayout(layout)


class MainWindow(QMainWindow):
    """Главное окно мессенджера"""
    
    def __init__(self, client: SyncShiftClient, username: str):
        super().__init__()
        self.client = client
        self.username = username
        self.current_chat = None
        self.messages = []
        self.init_ui()
        self.setup_handlers()
    
    def init_ui(self):
        self.setWindowTitle(f'SHIFT - {self.username}')
        self.setGeometry(100, 100, 900, 600)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Разделитель
        splitter = QSplitter(Qt.Horizontal)
        
        # Левая панель - список пользователей
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        # Заголовок списка
        users_header = QLabel('Пользователи')
        users_header.setFont(QFont('Arial', 14, QFont.Bold))
        left_layout.addWidget(users_header)
        
        # Список пользователей
        self.users_list = QListWidget()
        self.users_list.itemClicked.connect(self.select_user)
        self.users_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 3px;
            }
            QListWidget::item:hover {
                background-color: #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
        """)
        left_layout.addWidget(self.users_list)
        
        # Кнопка обновления списка
        refresh_btn = QPushButton('Обновить список')
        refresh_btn.clicked.connect(self.refresh_users)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        left_layout.addWidget(refresh_btn)
        
        # Правая панель - чат
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        # Заголовок чата
        self.chat_header = QLabel('Выберите чат')
        self.chat_header.setFont(QFont('Arial', 14, QFont.Bold))
        right_layout.addWidget(self.chat_header)
        
        # Область сообщений
        self.messages_area = QTextEdit()
        self.messages_area.setReadOnly(True)
        self.messages_area.setStyleSheet("""
            QTextEdit {
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 10px;
                background-color: #f5f5f5;
            }
        """)
        right_layout.addWidget(self.messages_area)
        
        # Поле ввода сообщения
        input_layout = QHBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText('Введите сообщение...')
        self.message_input.returnPressed.connect(self.send_message)
        self.message_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                font-size: 12px;
            }
        """)
        input_layout.addWidget(self.message_input)
        
        send_btn = QPushButton('Отправить')
        send_btn.clicked.connect(self.send_message)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        input_layout.addWidget(send_btn)
        
        right_layout.addLayout(input_layout)
        
        # Добавление панелей в разделитель
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([250, 650])
        
        main_layout.addWidget(splitter)
        
        # Статус бар
        self.statusBar().showMessage('Подключено к серверу')
    
    def setup_handlers(self):
        """Настройка обработчиков событий"""
        self.client.on('message', self.handle_message)
        self.client.on('message_sent', self.handle_message_sent)
        self.client.on('history', self.handle_history)
        self.client.on('users_list', self.handle_users_list)
        self.client.on('error', self.handle_error)
        
        # Запрос списка пользователей при запуске
        self.client.get_users_list()
    
    def refresh_users(self):
        """Обновление списка пользователей"""
        self.client.get_users_list()
    
    def select_user(self, item):
        """Выбор пользователя для чата"""
        self.current_chat = item.text()
        self.chat_header.setText(f'Чат с {self.current_chat}')
        self.messages_area.clear()
        self.messages = []
        
        # Запрос истории сообщений
        self.client.get_history(self.current_chat)
    
    def send_message(self):
        """Отправка сообщения"""
        if not self.current_chat:
            QMessageBox.warning(self, 'Ошибка', 'Выберите пользователя для чата')
            return
        
        content = self.message_input.text().strip()
        if not content:
            return
        
        self.client.send_message(self.current_chat, content)
        self.message_input.clear()
    
    def handle_message(self, data: dict):
        """Обработка входящего сообщения"""
        sender = data.get('sender')
        content = data.get('content')
        timestamp = data.get('timestamp', '')
        
        # Форматирование времени
        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime('%H:%M')
        except:
            formatted_time = timestamp
        
        # Если сообщение от текущего пользователя чата
        if sender == self.current_chat:
            self.add_message_to_chat(sender, content, formatted_time, is_own=False)
        else:
            # Уведомление о новом сообщении
            self.statusBar().showMessage(f'Новое сообщение от {sender}', 3000)
    
    def handle_message_sent(self, data: dict):
        """Обработка подтверждения отправки"""
        receiver = data.get('receiver')
        content = data.get('content')
        timestamp = data.get('timestamp', '')
        
        if receiver == self.current_chat:
            try:
                dt = datetime.fromisoformat(timestamp)
                formatted_time = dt.strftime('%H:%M')
            except:
                formatted_time = timestamp
            
            self.add_message_to_chat(self.username, content, formatted_time, is_own=True)
    
    def handle_history(self, data: dict):
        """Обработка истории сообщений"""
        messages = data.get('messages', [])
        
        # Очистка и отображение истории
        self.messages_area.clear()
        
        # Сообщения приходят в обратном порядке
        for msg in reversed(messages):
            sender = msg.get('sender')
            content = msg.get('content')
            timestamp = msg.get('timestamp', '')
            
            try:
                dt = datetime.fromisoformat(timestamp)
                formatted_time = dt.strftime('%H:%M')
            except:
                formatted_time = timestamp
            
            is_own = (sender == self.username)
            self.add_message_to_chat(sender, content, formatted_time, is_own)
    
    def handle_users_list(self, data: dict):
        """Обработка списка пользователей"""
        users = data.get('users', [])
        
        self.users_list.clear()
        for user in users:
            if user != self.username:  # Не показывать себя
                self.users_list.addItem(user)
    
    def handle_error(self, data: dict):
        """Обработка ошибок"""
        message = data.get('message', 'Неизвестная ошибка')
        QMessageBox.warning(self, 'Ошибка', message)
    
    def add_message_to_chat(self, sender: str, content: str, timestamp: str, is_own: bool):
        """Добавление сообщения в область чата"""
        html = f"""
        <div style="margin: 5px 0;">
            <span style="font-weight: bold; color: {'#4CAF50' if is_own else '#2196F3'};">{sender}</span>
            <span style="color: gray; font-size: 10px;">{timestamp}</span>
        </div>
        <div style="background-color: {'#dcf8c6' if is_own else '#ffffff'}; 
                    padding: 10px; 
                    border-radius: 10px; 
                    margin: 5px 0;
                    border: 1px solid #e0e0e0;
                    {'margin-left: 50px;' if is_own else 'margin-right: 50px;'}">
            {content}
        </div>
        """
        
        self.messages_area.insertHtml(html)
        # Прокрутка вниз
        scrollbar = self.messages_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        reply = QMessageBox.question(
            self, 'Выход',
            'Вы уверены, что хотите выйти?',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.client.disconnect()
            event.accept()
        else:
            event.ignore()


def main():
    """Запуск приложения"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Создание клиента
    client = SyncShiftClient()
    
    # Подключение к серверу
    if not client.connect():
        QMessageBox.critical(None, 'Ошибка', 'Не удалось подключиться к серверу')
        sys.exit(1)
    
    # Запуск цикла событий
    client.start_event_loop()
    
    # Диалог входа
    login_dialog = LoginDialog(client)
    if login_dialog.exec_() == QDialog.Accepted:
        # Главное окно
        main_window = MainWindow(client, login_dialog.username)
        main_window.show()
        sys.exit(app.exec_())
    else:
        client.disconnect()
        sys.exit(0)


if __name__ == '__main__':
    main()