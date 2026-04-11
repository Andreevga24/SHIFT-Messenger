"""
Скрипт для запуска клиента SHIFT Messenger
"""

import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from client.gui import main

if __name__ == '__main__':
    main()