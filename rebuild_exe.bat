@echo off
echo 🚀 Rebuilding Nyaa Auto Downloader executable...
echo.

REM Run the Python build script
python build_exe.py

REM Check if build was successful
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Build completed successfully!
    echo 📦 Executable: dist/Nyaa.si Anime Auto Downloader.exe
) else (
    echo.
    echo ❌ Build failed!
    echo Check the output above for error details.
)

echo.
pause


