@echo off
chcp 65001 >nul
title 原神帧率优化工具 - 可逆优化
color 0B
fltmc >nul 2>&1 || (
    echo 正在请求管理员权限...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

set "BACKUP=%USERPROFILE%\Desktop\原神优化备份_%date:/=-%_%time::=-%"
set "UNDO=%BACKUP%\撤销优化.bat"
md "%BACKUP%" 2>nul

echo ==============================================
echo          原神系统帧率优化（全部可逆）
echo 优化前自动备份注册表，撤销脚本存放：%UNDO%
echo ==============================================
pause
echo.

:: 初始化撤销脚本
echo @echo off > "%UNDO%"
echo chcp 65001 ^>nul >> "%UNDO%"
echo title 撤销原神优化 >> "%UNDO%"
echo echo 正在恢复全部修改... >> "%UNDO%"
echo. >> "%UNDO%"

:: 1. 备份并切换电源计划
for /f "tokens=2 delims=:(" %%a in ('powercfg /getactivescheme') do set OLD_POWER=%%a
for /f "tokens=1" %%g in ('powercfg -list ^| findstr "*"') do set OLD_POWER_GUID=%%g
echo powercfg /setactive %OLD_POWER_GUID% >> "%UNDO%"
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c >nul
if %errorlevel% equ 0 (echo [√] 已切换高性能电源计划) else echo [!] 切换高性能计划失败

:: 2. 游戏模式开启
reg query "HKCU\SOFTWARE\Microsoft\GameBar" /v AutoGameModeEnabled >nul 2>&1
if %errorlevel% equ 0 (
    for /f "skip=2 tokens=3" %%v in ('reg query "HKCU\SOFTWARE\Microsoft\GameBar" /v AutoGameModeEnabled') do echo reg add "HKCU\SOFTWARE\Microsoft\GameBar" /v AutoGameModeEnabled /t REG_DWORD /d %%v /f >> "%UNDO%"
) else (
    echo reg delete "HKCU\SOFTWARE\Microsoft\GameBar" /v AutoGameModeEnabled /f ^>nul 2^>^&1 >> "%UNDO%"
)
reg add "HKCU\SOFTWARE\Microsoft\GameBar" /v AutoGameModeEnabled /t REG_DWORD /d 1 /f >nul
echo [√] Windows游戏模式已开启

::3. 关闭GameDVR后台录制
reg query "HKCU\System\GameConfigStore" /v GameDVR_Enabled >nul 2>&1
if %errorlevel% equ 0 (
    for /f "skip=2 tokens=3" %%v in ('reg query "HKCU\System\GameConfigStore" /v GameDVR_Enabled') do echo reg add "HKCU\System\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d %%v /f >> "%UNDO%"
) else (
    echo reg delete "HKCU\System\GameConfigStore" /v GameDVR_Enabled /f ^>nul 2^>^&1 >> "%UNDO%"
)
reg add "HKCU\System\GameConfigStore" /v GameDVR_Enabled /t REG_DWORD /d 0 /f >nul

reg query "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR" /v AppCaptureEnabled >nul 2>&1
if %errorlevel% equ 0 (
    for /f "skip=2 tokens=3" %%v in ('reg query "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR" /v AppCaptureEnabled') do echo reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d %%v /f >> "%UNDO%"
) else (
    echo reg delete "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR" /v AppCaptureEnabled /f ^>nul 2^>^&1 >> "%UNDO%"
)
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 0 /f >nul
echo [√] Xbox游戏录制、后台捕获已关闭

::4. 关闭原神全屏优化（自动搜寻常见路径）
set "genshin_path="
for %%p in (
    "%ProgramFiles%\Genshin Impact\Genshin Impact Game\GenshinImpact.exe"
    "%ProgramFiles(x86)%\Genshin Impact\Genshin Impact Game\GenshinImpact.exe"
    "D:\Genshin Impact\Genshin Impact Game\GenshinImpact.exe"
    "E:\Genshin Impact\Genshin Impact Game\GenshinImpact.exe"
    "F:\Genshin Impact\Genshin Impact Game\GenshinImpact.exe"
) do if exist "%%p" set "genshin_path=%%p"

if defined genshin_path (
    reg query "HKCU\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers" /v "%genshin_path%" >nul 2>&1
    if %errorlevel% equ 0 (
        for /f "skip=2 tokens=3*" %%v in ('reg query "HKCU\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers" /v "%genshin_path%"') do echo reg add "HKCU\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers" /v "%genshin_path%" /t REG_SZ /d "%%v %%w" /f >> "%UNDO%"
    ) else (
        echo reg delete "HKCU\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers" /v "%genshin_path%" /f ^>nul 2^>^&1 >> "%UNDO%"
    )
    reg add "HKCU\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers" /v "%genshin_path%" /t REG_SZ /d DISABLEDXMAXIMIZEDWINDOWEDMODE /f >nul
    echo [√] 已禁用原神全屏优化（提升独占全屏性能）
) else (
    echo [!] 未自动找到GenshinImpact.exe
    echo 手动操作：找到GenshinImpact.exe →右键属性→兼容性→勾选【禁用全屏优化】
)

echo.
echo ==============================================
echo ✅ 优化全部执行完成！
echo 如需恢复所有设置：运行
echo %UNDO%
echo ==============================================
echo.
echo 📌 原神画面推荐设置（低配主机）
echo 显示模式：独占全屏
echo 渲染精度：0.7~0.8
echo 阴影质量：极低
echo 体积雾/反射/动态模糊：关闭
echo 垂直同步：关闭
echo 📌 笔记本务必插上电源运行游戏！
echo.
pause
exit