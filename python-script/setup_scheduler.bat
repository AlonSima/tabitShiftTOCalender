@echo off
REM setup_scheduler.bat - מגדיר Task Scheduler להריץ כל שבת 17:00
REM הרץ כ-Administrator!

echo ===================================
echo   TabitShift Sync - Task Scheduler
echo ===================================

REM מחפש את נתיב Python
for /f "tokens=*" %%i in ('where python') do set PYTHON_PATH=%%i
echo Python נמצא ב: %PYTHON_PATH%

REM נתיב לסקריפט (עדכן לפי המיקום שלך!)
set SCRIPT_DIR=%~dp0
set SCRIPT_PATH=%SCRIPT_DIR%tabit_sync.py

echo.
echo 📁 נתיב הסקריפט: %SCRIPT_PATH%
echo.

REM יצירת ה-Task
schtasks /create /tn "TabitShift-GoogleCalendar-Sync" ^
  /tr "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\"" ^
  /sc weekly ^
  /d SAT ^
  /st 17:00 ^
  /ru "%USERNAME%" ^
  /f

if %ERRORLEVEL% == 0 (
    echo.
    echo ✅ הצלחה! המשימה נוצרה:
    echo    שם: TabitShift-GoogleCalendar-Sync
    echo    זמן: כל שבת ב-17:00
    echo.
    echo לבדיקה ידנית:
    echo    schtasks /run /tn "TabitShift-GoogleCalendar-Sync"
    echo.
    echo לצפייה במשימה:
    echo    פתח Task Scheduler ^(taskschd.msc^)
) else (
    echo.
    echo ❌ שגיאה! בדוק שהרצת כ-Administrator
)

pause
