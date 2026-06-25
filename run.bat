@echo off
REM Запуск телеграм-бота заявок
cd /d "%~dp0"
if not exist ".env" (
    echo [!] Файл .env не найден.
    echo     Скопируй .env.example в .env и впиши BOT_TOKEN и ADMIN_CHAT_ID.
    pause
    exit /b 1
)
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" bot.py
pause
