@echo off
chcp 65001 >nul
rem ============================================================
rem EdanSpec Setup Script (Windows)
rem 将 EdanSpec 规范资产（单一规范源）按平台部署到目标项目目录，
rem 与 setup.sh 功能对等，供 Windows 原生 cmd.exe / PowerShell 使用，
rem 无需安装 bash / python。
rem   规范文档只维护一份 AGENTS.md，claudecode 部署时派生为 CLAUDE.md。
rem   claudecode -> {target}\.claude\   （AGENTS.md 派生为 CLAUDE.md + docs + rules + skills）
rem   opencode   -> {target}\.opencode\ （AGENTS.md + docs + rules + skills）+ {target}\opencode.json
rem Usage: setup.bat <target-dir> <platform>
rem   platform: claudecode | opencode
rem ============================================================

setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "TARGET_DIR=%~1"
set "PLATFORM=%~2"

rem ---- 参数校验 ----
if "%TARGET_DIR%"=="" goto usage
if "%PLATFORM%"=="" goto usage
if /i not "%PLATFORM%"=="claudecode" if /i not "%PLATFORM%"=="opencode" goto usage

rem ---- 校验源资产存在（按平台） ----
set "ASSETS=AGENTS.md docs rules skills"
if /i "%PLATFORM%"=="opencode" set "ASSETS=AGENTS.md docs rules skills opencode.json"
for %%A in (%ASSETS%) do (
    if not exist "%SCRIPT_DIR%%%A" (
        echo ERROR: 源资产不存在: %%A
        exit /b 1
    )
)

rem ---- 创建目标目录 ----
mkdir "%TARGET_DIR%" 2>nul

echo ============================================
echo   EdanSpec Setup
echo   Platform: %PLATFORM%
echo   Source:   %SCRIPT_DIR%
echo   Target:   %TARGET_DIR%
echo ============================================

if /i "%PLATFORM%"=="claudecode" goto do_claudecode
goto do_opencode

rem ------------------------------------------------------------
rem claudecode: AGENTS.md 派生为 CLAUDE.md，docs/rules/skills 复制到 .claude\
rem ------------------------------------------------------------
:do_claudecode
set "DEST=%TARGET_DIR%\.claude"
mkdir "%DEST%" 2>nul
copy /y "%SCRIPT_DIR%AGENTS.md" "%DEST%\CLAUDE.md" >nul
for %%D in (docs rules skills) do (
    xcopy "%SCRIPT_DIR%%%D" "%DEST%\%%D\" /e /i /y >nul
)
call :clean_ds_store "%DEST%"
echo Copied to %DEST% (AGENTS.md ^-^> CLAUDE.md)
goto done

rem ------------------------------------------------------------
rem opencode: AGENTS.md + docs/rules/skills 复制到 .opencode\，并生成 opencode.json
rem ------------------------------------------------------------
:do_opencode
set "DEST=%TARGET_DIR%\.opencode"
mkdir "%DEST%" 2>nul
copy /y "%SCRIPT_DIR%AGENTS.md" "%DEST%\AGENTS.md" >nul
for %%D in (docs rules skills) do (
    xcopy "%SCRIPT_DIR%%%D" "%DEST%\%%D\" /e /i /y >nul
)
call :clean_ds_store "%DEST%"
echo Copied to %DEST%
call :generate_opencode_json "%SCRIPT_DIR%opencode.json" "%TARGET_DIR%\opencode.json"
echo Generated %TARGET_DIR%\opencode.json
goto done

rem ------------------------------------------------------------
rem 生成部署版 opencode.json：改写 instructions 指向 .opencode\ 下资产。
rem 使用 Windows 自带 PowerShell（无需 python），写出无 BOM 的 UTF-8。
rem ------------------------------------------------------------
:generate_opencode_json
set "SRC_JSON=%~1"
set "DST_JSON=%~2"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=Get-Content -Raw -Encoding UTF8 $env:SRC_JSON|ConvertFrom-Json;$s.instructions=@('.opencode/AGENTS.md','.opencode/docs/**/*.md','.opencode/rules/**/*.md');$j=$s|ConvertTo-Json -Depth 10;[System.IO.File]::WriteAllText($env:DST_JSON,$j,(New-Object System.Text.UTF8Encoding($false)))"
exit /b 0

rem ------------------------------------------------------------
rem 递归删除复制产物中的 .DS_Store（macOS 元数据，Windows 上无用）
rem ------------------------------------------------------------
:clean_ds_store
set "TREE=%~1"
if "%TREE%"=="" exit /b 0
if exist "%TREE%\" for /r "%TREE%" %%F in (.DS_Store) do if exist "%%F" del /q "%%F" 2>nul
exit /b 0

rem ------------------------------------------------------------
:usage
echo.
echo Usage: setup.bat ^<target-dir^> ^<platform^>
echo.
echo   target-dir  目标项目目录（不存在则自动创建）
echo   platform    claudecode  - 部署到 {target}\.claude\（AGENTS.md 派生为 CLAUDE.md）
echo               opencode    - 部署到 {target}\.opencode\ + {target}\opencode.json
echo.
echo Examples:
echo   setup.bat C:\path\to\my-project claudecode
echo   setup.bat C:\path\to\my-project opencode
echo.
endlocal
exit /b 1

rem ------------------------------------------------------------
:done
echo.
echo Done! EdanSpec resources have been set up for %PLATFORM%.
echo.
if /i "%PLATFORM%"=="claudecode" (
    echo Next steps:
    echo   cd %TARGET_DIR%
    echo   claude                    # Start Claude Code
    echo   /skills                   # Verify skills are loaded
) else (
    echo Next steps:
    echo   cd %TARGET_DIR%
    echo   opencode                  # Start OpenCode
    echo   Verify skills are loaded in the session
)
endlocal
exit /b 0
