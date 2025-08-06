@echo off
echo ==================================================
echo      FinNews-Bot 本地端啟動器
echo ==================================================

REM 檢查 Python 是否存在
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 找不到 Python，請先安裝 Python 並將其加入到環境變數 PATH 中。
    pause
    exit /b
)

echo [INFO] 正在啟動 FinNews-Bot 主循環程式...
echo [INFO] 這個視窗將會持續顯示日誌。請不要關閉此視窗。

REM 執行主循環腳本
python scripts/run_local_loop.py

echo [INFO] 程式已結束。
pause
