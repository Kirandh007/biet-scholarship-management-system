@echo off
cd /d "%~dp0"
echo.
echo Starting Scholarship Management System...
echo Keep this window open while using the website.
echo Open this URL after the server starts:
echo http://127.0.0.1:8000
echo.

"C:\Users\kiran\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" server.py

echo.
echo Server stopped or failed to start.
echo If you see an error above, send a screenshot of this window.
pause
