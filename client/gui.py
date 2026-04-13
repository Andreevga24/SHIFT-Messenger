"""
SHIFT Messenger GUI
Графический интерфейс клиента мессенджера
"""

import os
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QListWidget, QListWidgetItem, QLabel,
    QDialog, QFormLayout, QMessageBox, QSplitter, QComboBox, QFrame, QScrollArea, QTextEdit,
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QEvent, QTimer

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)
from statuses import USER_STATUS_CHOICES
from PyQt5.QtGui import QFont, QColor, QBrush, QTextOption
from datetime import datetime
from client.client import SyncShiftClient

# Чёрно-синяя тёмная тема
_THEME = {
    'void': '#080b10',
    'bg': '#0f1419',
    'surface': '#141b26',
    'elevated': '#1a2332',
    'border': '#2a3a52',
    'text': '#e8eef7',
    'muted': '#7d92ad',
    'blue': '#2f6feb',
    'blue_hover': '#4a8ef7',
    'blue_soft': '#3d5a80',
    'accent_text': '#93c5fd',
    'bubble_own': '#152a45',
    'bubble_peer': '#161d2c',
    'unread_badge': '#f97316',
}


def _login_dialog_stylesheet() -> str:
    t = _THEME
    return f"""
        QDialog {{
            background-color: {t['bg']};
        }}
        QLabel {{
            color: {t['text']};
        }}
        QLineEdit {{
            background-color: {t['surface']};
            color: {t['text']};
            border: 1px solid {t['border']};
            border-radius: 6px;
            padding: 8px;
        }}
        QLineEdit:focus {{
            border: 1px solid {t['blue']};
        }}
        QPushButton {{
            color: {t['text']};
            padding: 10px;
            border-radius: 6px;
            font-size: 14px;
            border: none;
        }}
        QPushButton:hover {{
            background-color: {t['blue_hover']};
        }}
        QPushButton#loginPrimary {{
            background-color: {t['blue']};
        }}
        QPushButton#loginPrimary:hover {{
            background-color: {t['blue_hover']};
        }}
        QPushButton#loginSecondary {{
            background-color: {t['elevated']};
            border: 1px solid {t['blue_soft']};
        }}
        QPushButton#loginSecondary:hover {{
            background-color: {t['surface']};
            border: 1px solid {t['blue']};
        }}
    """


def _main_window_stylesheet() -> str:
    t = _THEME
    return f"""
        QMainWindow {{
            background-color: {t['bg']};
        }}
        QWidget {{
            color: {t['text']};
        }}
        QLabel {{
            color: {t['text']};
        }}
        QListWidget {{
            background-color: {t['surface']};
            color: {t['text']};
            border: 1px solid {t['border']};
            border-radius: 6px;
            padding: 6px;
        }}
        QListWidget::item {{
            padding: 8px;
            border-radius: 4px;
        }}
        QListWidget::item:hover {{
            background-color: {t['elevated']};
        }}
        QListWidget::item:selected {{
            background-color: {t['blue']};
            color: {t['text']};
        }}
        QScrollArea#messagesScroll {{
            background-color: {t['void']};
            border: 1px solid {t['border']};
            border-radius: 6px;
        }}
        QScrollArea#messagesScroll > QWidget > QWidget {{
            background-color: {t['void']};
        }}
        QLineEdit {{
            background-color: {t['surface']};
            color: {t['text']};
            border: 1px solid {t['border']};
            border-radius: 6px;
            padding: 10px;
            font-size: 12px;
        }}
        QLineEdit:focus {{
            border: 1px solid {t['blue']};
        }}
        QPushButton {{
            color: {t['text']};
            padding: 8px 14px;
            border-radius: 6px;
            border: none;
        }}
        QPushButton#actionRefresh {{
            background-color: {t['blue']};
        }}
        QPushButton#actionRefresh:hover {{
            background-color: {t['blue_hover']};
        }}
        QPushButton#actionLogout {{
            background-color: {t['elevated']};
            border: 1px solid {t['blue_soft']};
        }}
        QPushButton#actionLogout:hover {{
            border: 1px solid {t['blue']};
            background-color: {t['surface']};
        }}
        QPushButton#actionSend {{
            background-color: {t['blue']};
            padding: 10px 20px;
        }}
        QPushButton#actionSend:hover {{
            background-color: {t['blue_hover']};
        }}
        QStatusBar {{
            background-color: {t['surface']};
            color: {t['muted']};
            border-top: 1px solid {t['border']};
        }}
        QSplitter::handle {{
            background-color: {t['border']};
            width: 2px;
        }}
        QComboBox {{
            background-color: {t['surface']};
            color: {t['text']};
            border: 1px solid {t['border']};
            border-radius: 6px;
            padding: 8px 10px;
            min-height: 20px;
        }}
        QComboBox:hover {{
            border: 1px solid {t['blue_soft']};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 28px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {t['elevated']};
            color: {t['text']};
            selection-background-color: {t['blue']};
            border: 1px solid {t['border']};
        }}
    """


def _app_dialog_stylesheet() -> str:
    t = _THEME
    return f"""
        QMessageBox {{
            background-color: {t['surface']};
        }}
        QMessageBox QLabel {{
            color: {t['text']};
        }}
        QMessageBox QPushButton {{
            background-color: {t['blue']};
            color: {t['text']};
            padding: 6px 18px;
            border-radius: 4px;
            min-width: 72px;
        }}
        QMessageBox QPushButton:hover {{
            background-color: {t['blue_hover']};
        }}
    """


class SignalHandler(QObject):
    """Обработчик сигналов для безопасного обновления GUI из другого потока"""
    message_received = pyqtSignal(dict)
    message_sent = pyqtSignal(dict)
    history_received = pyqtSignal(dict)
    users_list_received = pyqtSignal(dict)
    user_status_received = pyqtSignal(dict)
    unread_counts_received = pyqtSignal(dict)
    error_received = pyqtSignal(dict)


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
        title.setStyleSheet(f"color: {_THEME['accent_text']};")
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
        self.login_btn.setObjectName('loginPrimary')
        self.login_btn.clicked.connect(self.login)
        
        self.register_btn = QPushButton('Регистрация')
        self.register_btn.setObjectName('loginSecondary')
        self.register_btn.clicked.connect(self.register)
        
        button_layout.addWidget(self.login_btn)
        button_layout.addWidget(self.register_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.setStyleSheet(_login_dialog_stylesheet())
    
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


class MainWindow(QMainWindow):
    """Главное окно мессенджера"""
    
    def __init__(self, client: SyncShiftClient, username: str):
        super().__init__()
        self.client = client
        self.username = username
        self.current_chat = None
        self.messages = []
        self.peer_statuses: dict = {}
        self._users_order: list = []
        self.unread_counts: dict = {}
        self.signal_handler = SignalHandler()
        self.init_ui()
        self.setup_handlers()
        self.setup_signal_connections()
    
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
        self.users_header = QLabel('Пользователи')
        self.users_header.setFont(QFont('Arial', 14, QFont.Bold))
        left_layout.addWidget(self.users_header)
        
        status_row = QHBoxLayout()
        status_row.addWidget(QLabel('Мой статус:'))
        self.status_combo = QComboBox()
        self.status_combo.addItems(list(USER_STATUS_CHOICES))
        self.status_combo.blockSignals(True)
        self.status_combo.setCurrentText(self.client.get_current_status())
        self.status_combo.blockSignals(False)
        self.status_combo.currentTextChanged.connect(self._on_my_status_changed)
        status_row.addWidget(self.status_combo, stretch=1)
        left_layout.addLayout(status_row)
        
        # Список пользователей
        self.users_list = QListWidget()
        self.users_list.itemClicked.connect(self.select_user)
        left_layout.addWidget(self.users_list)
        
        # Кнопка обновления списка
        refresh_btn = QPushButton('Обновить список')
        refresh_btn.setObjectName('actionRefresh')
        refresh_btn.clicked.connect(self.refresh_users)
        left_layout.addWidget(refresh_btn)

        self.logout_btn = QPushButton('Выйти из аккаунта')
        self.logout_btn.setObjectName('actionLogout')
        self.logout_btn.clicked.connect(self.logout_from_account)
        left_layout.addWidget(self.logout_btn)
        
        # Правая панель - чат
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        # Заголовок чата
        self.chat_header = QLabel('Выберите чат')
        self.chat_header.setFont(QFont('Arial', 14, QFont.Bold))
        right_layout.addWidget(self.chat_header)
        
        # Область сообщений: QScrollArea + QFrame (скругление в стилях Qt, не HTML в QTextEdit)
        self.messages_scroll = QScrollArea()
        self.messages_scroll.setObjectName('messagesScroll')
        self.messages_scroll.setWidgetResizable(True)
        self.messages_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.messages_scroll.setFrameShape(QFrame.NoFrame)
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(8, 8, 8, 8)
        self.messages_layout.setSpacing(6)
        self.messages_scroll.setWidget(self.messages_container)
        right_layout.addWidget(self.messages_scroll, stretch=1)
        self.messages_viewport = self.messages_scroll.viewport()
        self.messages_viewport.installEventFilter(self)
        
        # Поле ввода сообщения
        input_layout = QHBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText('Введите сообщение...')
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)
        
        send_btn = QPushButton('Отправить')
        send_btn.setObjectName('actionSend')
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)
        
        right_layout.addLayout(input_layout)
        
        # Добавление панелей в разделитель
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([250, 650])
        
        main_layout.addWidget(splitter)
        
        # Статус бар
        self.statusBar().showMessage('Подключено к серверу')
        self.setStyleSheet(_main_window_stylesheet())
    
    def setup_handlers(self):
        """Настройка обработчиков событий"""
        self.client.on('message', lambda data: self.signal_handler.message_received.emit(data))
        self.client.on('message_sent', lambda data: self.signal_handler.message_sent.emit(data))
        self.client.on('history', lambda data: self.signal_handler.history_received.emit(data))
        self.client.on('users_list', lambda data: self.signal_handler.users_list_received.emit(data))
        self.client.on('user_status', lambda data: self.signal_handler.user_status_received.emit(data))
        self.client.on('unread_counts', lambda data: self.signal_handler.unread_counts_received.emit(data))
        self.client.on('error', lambda data: self.signal_handler.error_received.emit(data))
        
        # Запрос списка пользователей при запуске
        self.client.get_users_list()
    
    def setup_signal_connections(self):
        """Подключение сигналов к слотам"""
        self.signal_handler.message_received.connect(self._handle_message_safe)
        self.signal_handler.message_sent.connect(self._handle_message_sent_safe)
        self.signal_handler.history_received.connect(self._handle_history_safe)
        self.signal_handler.users_list_received.connect(self._handle_users_list_safe)
        self.signal_handler.user_status_received.connect(self._handle_user_status_safe)
        self.signal_handler.unread_counts_received.connect(self._handle_unread_counts_safe)
        self.signal_handler.error_received.connect(self._handle_error_safe)
    
    def _handle_message_safe(self, data: dict):
        """Безопасная обработка входящего сообщения"""
        sender = data.get('sender')
        content = data.get('content')
        timestamp = data.get('timestamp', '')
        
        # Форматирование времени
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = dt.strftime('%H:%M')
        except (ValueError, TypeError):
            formatted_time = str(timestamp) if timestamp else ''
        
        # Если сообщение от текущего пользователя чата
        if sender == self.current_chat:
            self.add_message_to_chat(sender, content, formatted_time, is_own=False)
            self.client.mark_read(sender)
        else:
            # Уведомление о новом сообщении
            self.statusBar().showMessage(f'Новое сообщение от {sender}', 3000)
    
    def _handle_message_sent_safe(self, data: dict):
        """Безопасная обработка подтверждения отправки"""
        receiver = data.get('receiver')
        content = data.get('content')
        timestamp = data.get('timestamp', '')
        
        if receiver == self.current_chat:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%H:%M')
            except (ValueError, TypeError):
                formatted_time = str(timestamp) if timestamp else ''
            
            self.add_message_to_chat(self.username, content, formatted_time, is_own=True)
    
    def _handle_history_safe(self, data: dict):
        """Безопасная обработка истории сообщений"""
        messages = data.get('messages', [])
        
        # Очистка и отображение истории
        self._clear_messages_layout()
        
        # Сообщения приходят в обратном порядке
        for msg in reversed(messages):
            sender = msg.get('sender')
            content = msg.get('content')
            timestamp = msg.get('timestamp', '')
            
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%H:%M')
            except (ValueError, TypeError):
                formatted_time = str(timestamp) if timestamp else ''
            
            is_own = (sender == self.username)
            self.add_message_to_chat(sender, content, formatted_time, is_own)
    
    def _handle_users_list_safe(self, data: dict):
        """Безопасная обработка списка пользователей"""
        users = data.get('users', [])
        self._users_order = [u for u in users if u != self.username]
        for u, st in (data.get('statuses') or {}).items():
            self.peer_statuses[u] = st
        self.unread_counts = {
            str(k): int(v)
            for k, v in (data.get('unread_counts') or {}).items()
        }
        self._render_users_list()
    
    def _handle_unread_counts_safe(self, data: dict):
        """Обновление счётчиков непрочитанных с сервера."""
        self.unread_counts = {
            str(k): int(v)
            for k, v in (data.get('counts') or {}).items()
        }
        self._render_users_list()
    
    def _handle_user_status_safe(self, data: dict):
        """Обновление статуса контакта в реальном времени."""
        u = data.get('user')
        st = data.get('status')
        if u is None or st is None:
            return
        self.peer_statuses[u] = st
        if u == self.username:
            self._sync_status_combo(self.client.get_current_status())
        self._render_users_list()
    
    def _handle_error_safe(self, data: dict):
        """Безопасная обработка ошибок"""
        message = data.get('message', 'Неизвестная ошибка')
        QMessageBox.warning(self, 'Ошибка', message)
    
    def refresh_users(self):
        """Обновление списка пользователей"""
        self.client.get_users_list()
    
    def _sync_status_combo(self, status: str):
        self.status_combo.blockSignals(True)
        idx = self.status_combo.findText(status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)
        self.status_combo.blockSignals(False)
    
    def _on_my_status_changed(self, status: str):
        if not status:
            return
        self.client.set_status(status)
    
    def _update_users_header_badge(self):
        total = sum(self.unread_counts.values())
        if total:
            self.users_header.setText(f'Пользователи · {total} непрочит.')
        else:
            self.users_header.setText('Пользователи')
    
    def _render_users_list(self):
        self.users_list.blockSignals(True)
        self.users_list.clear()
        for u in self._users_order:
            st = self.peer_statuses.get(u, 'не в сети')
            n_unread = int(self.unread_counts.get(u, 0))
            badge = f'  [{n_unread} непр.]' if n_unread > 0 else ''
            label = f"{u} — {st}{badge}"
            it = QListWidgetItem(label)
            it.setData(Qt.UserRole, u)
            if n_unread > 0:
                it.setForeground(QBrush(QColor(_THEME['unread_badge'])))
            self.users_list.addItem(it)
        if self.current_chat:
            for i in range(self.users_list.count()):
                row = self.users_list.item(i)
                if row and row.data(Qt.UserRole) == self.current_chat:
                    self.users_list.setCurrentRow(i)
                    break
        self.users_list.blockSignals(False)
        self._update_users_header_badge()

    def logout_from_account(self):
        """Выход из аккаунта с сохранением подключения к серверу для повторного входа"""
        reply = QMessageBox.question(
            self,
            'Выход из аккаунта',
            'Выйти из аккаунта? Сообщения на экране будут очищены.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self.client.disconnect()
        if not self.client.connect():
            QMessageBox.critical(
                self,
                'Ошибка',
                'Не удалось снова подключиться к серверу. Приложение будет закрыто.',
            )
            self.client.stop_event_loop()
            self.close()
            return

        login_dialog = LoginDialog(self.client)
        if login_dialog.exec_() != QDialog.Accepted:
            self.client.disconnect()
            self.client.stop_event_loop()
            self.close()
            QApplication.instance().quit()
            return

        self.username = login_dialog.username
        self.setWindowTitle(f'SHIFT - {self.username}')
        self.current_chat = None
        self.messages = []
        self.peer_statuses.clear()
        self._users_order.clear()
        self.unread_counts.clear()
        self.users_list.clear()
        self._clear_messages_layout()
        self.chat_header.setText('Выберите чат')
        self.message_input.clear()
        self._sync_status_combo(self.client.get_current_status())
        self.statusBar().showMessage('Подключено к серверу')
        self.client.get_users_list()
    
    def select_user(self, item):
        """Выбор пользователя для чата"""
        name = item.data(Qt.UserRole)
        self.current_chat = name if name is not None else item.text().split(' — ')[0]
        self.chat_header.setText(f'Чат с {self.current_chat}')
        self._clear_messages_layout()
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
    
    def eventFilter(self, obj, event):
        if getattr(self, 'messages_viewport', None) is obj and event.type() == QEvent.Resize:
            self._apply_bubble_max_widths()
        return super().eventFilter(obj, event)
    
    def _max_bubble_width(self) -> int:
        if not getattr(self, 'messages_scroll', None):
            return 400
        return max(200, int(self.messages_scroll.viewport().width() * 0.75))
    
    def _apply_bubble_max_widths(self):
        mw = self._max_bubble_width()
        for frame in self.messages_container.findChildren(QFrame):
            if frame.objectName() == 'chatBubble':
                frame.setMaximumWidth(mw)
        QTimer.singleShot(0, self._reflow_message_bodies)
    
    def _sync_msg_body_height(self, body: QTextEdit):
        """Перенос по символам + высота под содержимое после смены ширины."""
        w = body.viewport().width()
        if w <= 0:
            return
        body.document().setTextWidth(w)
        margins = body.contentsMargins()
        extra = body.frameWidth() * 2 + 4
        h = int(body.document().size().height()) + margins.top() + margins.bottom() + extra
        body.setFixedHeight(max(h, 28))
    
    def _reflow_message_bodies(self):
        for body in self.messages_container.findChildren(QTextEdit):
            if body.objectName() == 'msgBody':
                self._sync_msg_body_height(body)
    
    def _clear_messages_layout(self):
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
    
    def _scroll_messages_to_bottom(self):
        bar = self.messages_scroll.verticalScrollBar()
        QTimer.singleShot(0, lambda b=bar: b.setValue(b.maximum()))
    
    def add_message_to_chat(self, sender: str, content: str, timestamp: str, is_own: bool):
        """Пузырь из QFrame + stylesheet: скругление реально рисуется Qt. Ширина до 75% поля; свои справа."""
        t = _THEME
        name_hex = '#7dd3fc' if is_own else t['accent_text']
        bubble_bg = t['bubble_own'] if is_own else t['bubble_peer']
        border_c = '#2563eb' if is_own else t['border']

        bubble = QFrame()
        bubble.setObjectName('chatBubble')
        bubble.setAttribute(Qt.WA_StyledBackground, True)
        bubble.setStyleSheet(f"""
            QFrame#chatBubble {{
                background-color: {bubble_bg};
                border: 1px solid {border_c};
                border-radius: 40px;
            }}
        """)

        inner = QVBoxLayout(bubble)
        inner.setContentsMargins(22, 18, 22, 20)
        inner.setSpacing(10)

        head = QHBoxLayout()
        head.setSpacing(10)
        name_lbl = QLabel(sender or '')
        name_lbl.setStyleSheet(f'color: {name_hex}; font-weight: 600; font-size: 13px;')
        time_lbl = QLabel(str(timestamp or ''))
        time_lbl.setStyleSheet(f"color: {t['muted']}; font-size: 11px;")
        head.addWidget(name_lbl, 0, Qt.AlignLeft | Qt.AlignVCenter)
        head.addWidget(time_lbl, 0, Qt.AlignLeft | Qt.AlignVCenter)
        head.addStretch(1)
        head_w = QWidget()
        head_w.setLayout(head)
        head_w.setStyleSheet('background: transparent;')
        inner.addWidget(head_w)

        body_te = QTextEdit()
        body_te.setObjectName('msgBody')
        body_te.setReadOnly(True)
        body_te.setFrameShape(QFrame.NoFrame)
        body_te.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        body_te.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        body_te.setLineWrapMode(QTextEdit.WidgetWidth)
        body_te.setWordWrapMode(QTextOption.WrapAnywhere)
        body_te.document().setDocumentMargin(0)
        body_te.setPlainText(content or '')
        body_te.setTextInteractionFlags(Qt.TextSelectableByMouse)
        body_te.setStyleSheet(
            f"QTextEdit {{ color: {t['text']}; font-size: 13px; background: transparent; "
            f"border: none; padding: 0px; }}"
        )
        body_te.document().documentLayout().documentSizeChanged.connect(
            lambda _=None, b=body_te: self._sync_msg_body_height(b)
        )
        inner.addWidget(body_te)

        bubble.setMaximumWidth(self._max_bubble_width())

        row = QWidget()
        row.setStyleSheet('background: transparent;')
        hl = QHBoxLayout(row)
        hl.setContentsMargins(4, 4, 4, 4)
        hl.setSpacing(0)
        if is_own:
            hl.addStretch(1)
            hl.addWidget(bubble, 0, Qt.AlignTop)
        else:
            hl.addWidget(bubble, 0, Qt.AlignTop)
            hl.addStretch(1)

        self.messages_layout.addWidget(row)
        QTimer.singleShot(0, lambda b=body_te: self._sync_msg_body_height(b))
        self._scroll_messages_to_bottom()
    
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        reply = QMessageBox.question(
            self, 'Выход',
            'Вы уверены, что хотите выйти?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.client.disconnect()
            self.client.stop_event_loop()
            event.accept()
        else:
            event.ignore()


def main():
    """Запуск приложения"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet(_app_dialog_stylesheet())
    
    # Создание клиента
    client = SyncShiftClient()
    
    # Запуск цикла событий ДО подключения
    client.start_event_loop()
    
    # Подключение к серверу
    if not client.connect():
        QMessageBox.critical(None, 'Ошибка', 'Не удалось подключиться к серверу')
        client.stop_event_loop()
        sys.exit(1)
    
    # Диалог входа
    login_dialog = LoginDialog(client)
    if login_dialog.exec_() == QDialog.Accepted:
        # Главное окно
        main_window = MainWindow(client, login_dialog.username)
        main_window.show()
        sys.exit(app.exec_())
    else:
        client.disconnect()
        client.stop_event_loop()
        sys.exit(0)


if __name__ == '__main__':
    main()