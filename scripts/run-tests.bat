@echo off
REM Test Runner Batch Script for Windows
REM This script provides a simple interface to run tests on Windows systems

setlocal enabledelayedexpansion

REM Colors (limited in batch)
set "GREEN=[92m"
set "RED=[91m"
set "BLUE=[94m"
set "YELLOW=[93m"
set "NC=[0m"

REM Default values
set "SERVICE=all"
set "COVERAGE=false"

REM Parse arguments
:parse_args
if "%~1"=="" goto :main
if /i "%~1"=="user" set "SERVICE=user" & shift & goto :parse_args
if /i "%~1"=="task" set "SERVICE=task" & shift & goto :parse_args
if /i "%~1"=="notification" set "SERVICE=notification" & shift & goto :parse_args
if /i "%~1"=="frontend" set "SERVICE=frontend" & shift & goto :parse_args
if /i "%~1"=="all" set "SERVICE=all" & shift & goto :parse_args
if /i "%~1"=="--coverage" set "COVERAGE=true" & shift & goto :parse_args
if /i "%~1"=="--help" goto :show_help
shift
goto :parse_args

:show_help
echo Usage: %~nx0 [service] [options]
echo.
echo Services:
echo   user          Run user service tests
echo   task          Run task service tests
echo   notification  Run notification service tests
echo   frontend      Run frontend tests
echo   all           Run all service tests (default)
echo.
echo Options:
echo   --coverage    Run with coverage reporting
echo   --help        Show this help message
goto :eof

:main
echo %BLUE%=== Microservices Task Management Test Suite ===%NC%
echo Starting test execution for: %SERVICE%

if /i "%SERVICE%"=="user" goto :test_user
if /i "%SERVICE%"=="task" goto :test_task
if /i "%SERVICE%"=="notification" goto :test_notification
if /i "%SERVICE%"=="frontend" goto :test_frontend
if /i "%SERVICE%"=="all" goto :test_all

:test_user
echo %BLUE%Running User Service tests...%NC%
cd user-service
if "%COVERAGE%"=="true" (
    pytest tests/ --cov=app --cov-report=term-missing -v
) else (
    pytest tests/ -v
)
if errorlevel 1 (
    echo %RED%User Service tests failed%NC%
    cd ..
    exit /b 1
)
echo %GREEN%User Service tests passed%NC%
cd ..
if /i "%SERVICE%"=="user" goto :success
goto :test_task

:test_task
echo %BLUE%Running Task Service tests...%NC%
cd task-service
if "%COVERAGE%"=="true" (
    pytest tests/ --cov=app --cov-report=term-missing -v
) else (
    pytest tests/ -v
)
if errorlevel 1 (
    echo %RED%Task Service tests failed%NC%
    cd ..
    exit /b 1
)
echo %GREEN%Task Service tests passed%NC%
cd ..
if /i "%SERVICE%"=="task" goto :success
goto :test_notification

:test_notification
echo %BLUE%Running Notification Service tests...%NC%
cd notification-service
if "%COVERAGE%"=="true" (
    pytest tests/ --cov=app --cov-report=term-missing -v
) else (
    pytest tests/ -v
)
if errorlevel 1 (
    echo %RED%Notification Service tests failed%NC%
    cd ..
    exit /b 1
)
echo %GREEN%Notification Service tests passed%NC%
cd ..
if /i "%SERVICE%"=="notification" goto :success
goto :test_frontend

:test_frontend
echo %BLUE%Running Frontend tests...%NC%
cd frontend
if "%COVERAGE%"=="true" (
    npm run test:coverage
) else (
    npm run test
)
if errorlevel 1 (
    echo %RED%Frontend tests failed%NC%
    cd ..
    exit /b 1
)
echo %GREEN%Frontend tests passed%NC%
cd ..
if /i "%SERVICE%"=="frontend" goto :success
goto :success

:test_all
call :test_user
call :test_task
call :test_notification
call :test_frontend
goto :success

:success
echo.
echo %GREEN%All selected tests completed successfully!%NC%
exit /b 0