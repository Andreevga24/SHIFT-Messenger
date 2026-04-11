"""
Диагностический скрипт для клиента
"""

import sys
import os
import traceback

print("=" * 50)
print("SHIFT Messenger - Диагностика клиента")
print("=" * 50)

# Проверка Python
print(f"\n✓ Python версия: {sys.version}")

# Проверка текущей директории
print(f"✓ Текущая директория: {os.getcwd()}")

# Проверка PyQt5
try:
    from PyQt5.QtWidgets import QApplication
    print("✓ PyQt5 установлен")
except Exception as e:
    print(f"✗ Ошибка PyQt5: {e}")
    traceback.print_exc()
    input("Нажмите Enter для выхода...")
    sys.exit(1)

# Проверка websockets
try:
    import websockets
    print("✓ websockets установлен")
except Exception as e:
    print(f"✗ Ошибка websockets: {e}")
    traceback.print_exc()
    input("Нажмите Enter для выхода...")
    sys.exit(1)

# Проверка импорта клиента
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from client.client import SyncShiftClient
    print("✓ client.client импортирован")
except Exception as e:
    print(f"✗ Ошибка импорта client.client: {e}")
    traceback.print_exc()
    input("Нажмите Enter для выхода...")
    sys.exit(1)

# Проверка импорта GUI
try:
    from client.gui import main
    print("✓ client.gui импортирован")
except Exception as e:
    print(f"✗ Ошибка импорта client.gui: {e}")
    traceback.print_exc()
    input("Нажмите Enter для выхода...")
    sys.exit(1)

print("\n" + "=" * 50)
print("Все проверки пройдены! Запуск клиента...")
print("=" * 50 + "\n")

try:
    main()
except Exception as e:
    print(f"\n✗ Ошибка при запуске: {e}")
    traceback.print_exc()
    input("\nНажмите Enter для выхода...")