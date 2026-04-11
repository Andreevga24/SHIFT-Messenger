@echo off
chcp 65001 >nul
echo ========================================
echo SHIFT Messenger - Запуск сервера
echo ========================================
echo.
echo Сервер запускается на localhost:8765
echo Не закрывайте это окно!
echo.
python run_server.py
pause