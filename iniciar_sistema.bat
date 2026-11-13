@echo off
chcp 65001 >nul
title SISTEMA IA - Aula Virtual y Prediccion de Riesgo Academico
cd /d "%~dp0"

echo ===========================================================================
echo       SISTEMA INTELIGENTE DE COMPUTACION Y PREDICCION ACADEMICA (IA)
echo ===========================================================================
echo.
echo  [1/3] Verificando entorno de ejecucion...

set "PYTHON_EXE=.\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
)

echo  [2/3] Comprobando disponibilidad de base de datos...
"%PYTHON_EXE%" -c "from services.db_service import get_connection; conn = get_connection(); conn.close()" >nul 2>&1
if %errorlevel% neq 0 (
    echo        ^! Base de datos PostgreSQL no detectada con las credenciales de .env.
    echo        ^! Activando automaticamente MODO DEMOSTRACION (USE_MOCK_DATA=true).
    echo        ^! El sistema cargara los datos preconfigurados para la presentacion.
    set "USE_MOCK_DATA=true"
) else (
    echo        * Conexion exitosa con base de datos PostgreSQL.
)

echo.
echo  [3/3] Iniciando servidor Flask local...
echo.
echo  -------------------------------------------------------------------------
echo   ACCESOS DIRECTOS PARA DEMOSTRACION (JURADO / EVALUADOR):
echo   * Rol Estudiante:  Usuario: alumno1     / Contrasena: Alumno123
echo  -------------------------------------------------------------------------
echo.
echo   La aplicacion se abrira en su navegador en: http://127.0.0.1:5000/login
echo   Para detener el sistema, presione [Ctrl + C] en esta ventana.
echo.
echo ===========================================================================

:: Abrir el navegador automaticamente tras 2 segundos
start /b powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:5000/login'" >nul 2>&1

:: Iniciar la aplicacion Flask
"%PYTHON_EXE%" app.py

pause
