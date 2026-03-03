@echo off
chcp 65001 > nul
echo ====================================================
echo       جاري تحويل برنامج المحكمة الشرعية إلى EXE
echo ====================================================
echo.

:: البحث عن مسار بايثون
set PY_CMD=python
py --version >nul 2>&1
if %errorlevel% == 0 (set PY_CMD=py)

echo [1/3] التأكد من وجود مكتبة PyInstaller باستخدام (%PY_CMD%)...
%PY_CMD% -m pip install pyinstaller --quiet

:: 2. تنظيف المجلدات القديمة
echo [2/3] تنظيف مخلفات التحويل القديمة...
if exist build rd /s /q build
if exist dist rd /s /q dist

:: 3. البدء بعملية التحويل
echo [3/3] جاري بناء البرنامج (قد يستغرق هذا دقيقة)...
echo.
%PY_CMD% -m PyInstaller --noconfirm --onedir --windowed ^
 --add-data "fonts;fonts" ^
 --add-data "icons;icons" ^
 --add-data "files;files" ^
 --add-data "*.ui;." ^
 --name "Courts_System" ^
 --clean ^
 app.py

echo.
echo ====================================================
echo       تمت العملية بنجاح!
echo       اذهب لمجلد (dist) ستجد داخله مجلد (Courts_System)
echo       هذا هو المجلد الذي تنسخه لأجهزة الموظفين.
echo       شغل البرنامج من ملف: Courts_System.exe
echo ====================================================
pause
