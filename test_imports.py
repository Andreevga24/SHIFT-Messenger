"""
Тестовый скрипт для проверки импортов
"""

import sys
import os

print("Python path:", sys.path[:3])
print("Current directory:", os.getcwd())

try:
    print("\nПроверка импорта PyQt5...")
    from PyQt5.QtWidgets import QApplication
    print("✅ PyQt5 импортирован успешно")
except Exception as e:
    print(f"❌ Ошибка импорта PyQt5: {e}")

try:
    print("\nПроверка импорта websockets...")
    import websockets
    print("✅ websockets импортирован успешно")
except Exception as e:
    print(f"❌ Ошибка импорта websockets: {e}")

try:
    print("\nПроверка импорта client.client...")
    from client.client import SyncShiftClient
    print("✅ client.client импортирован успешно")
except Exception as e:
    print(f"❌ Ошибка импорта client.client: {e}")

try:
    print("\nПроверка импорта client.gui...")
    from client.gui import main
    print("✅ client.gui импортирован успешно")
except Exception as e:
    print(f"❌ Ошибка импорта client.gui: {e}")

print("\nВсе проверки завершены!")