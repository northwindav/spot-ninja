@REM build_docker.bat - Build WindNinja Docker image for Spot-Ninja (Windows)
@REM Usage: docker\build_docker.bat [--tag windninja:latest] [--no-cache]

@echo off
setlocal enabledelayedexpansion

REM Parse arguments
set TAG=windninja:latest
set BUILD_ARGS=

:parse_args
if "%~1"=="" goto :build
if "%~1"=="--tag" (
    set TAG=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--no-cache" (
    set BUILD_ARGS=!BUILD_ARGS! --no-cache
    shift
    goto :parse_args
)

:build
echo ==========================================
echo Building WindNinja Docker image
echo ==========================================
echo Tag:  %TAG%
echo Args: %BUILD_ARGS%
echo.

REM Check if Dockerfile exists
if not exist "docker\Dockerfile" (
    echo ERROR: docker\Dockerfile not found. Run from project root.
    exit /b 1
)

REM Check if WindNinja source exists
set WINDNINJA_DIR=windninja_source
if not exist "%WINDNINJA_DIR%" (
    echo Cloning WindNinja source...
    git clone https://github.com/firelab/windninja.git %WINDNINJA_DIR%
    if errorlevel 1 (
        echo ERROR: Failed to clone WindNinja repository.
        exit /b 1
    )
) else (
    echo Using existing WindNinja source at %WINDNINJA_DIR%
)

REM Build the image
echo.
echo Running: docker build -t %TAG% %BUILD_ARGS% -f docker\Dockerfile %WINDNINJA_DIR%
docker build -t %TAG% %BUILD_ARGS% -f docker\Dockerfile %WINDNINJA_DIR%
if errorlevel 1 (
    echo ERROR: Docker build failed.
    exit /b 1
)

echo.
echo ==========================================
echo Build complete!
echo Tag: %TAG%
echo.
echo Verify build:
echo   docker run --rm %TAG% windninja --help
echo.
echo Run with data:
echo   docker run -v %%cd%%\data:/data %TAG% windninja /data/config.sta
echo ==========================================
