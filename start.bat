@echo off
echo ============================================================
echo   Dharma Legal Chatbot — Startup Script
echo ============================================================

REM Paths
SET VENV=%~dp0.venv
SET PROJECT=%~dp0AI-Legal-Chatbot
SET PYTHON=%VENV%\Scripts\python.exe

echo.
echo [1/4] Checking virtual environment...
IF NOT EXIST "%PYTHON%" (
    echo ERROR: Virtual environment not found at %VENV%
    echo Please create it with: python -m venv .venv
    echo Then install packages: .venv\Scripts\pip install -r AI-Legal-Chatbot\requirements.txt
    pause
    exit /b 1
)

echo [2/4] Checking FAISS index...
IF NOT EXIST "%PROJECT%\data\vector_db\legal_index.faiss" (
    echo Building FAISS index (first time setup — this may take several minutes)...
    cd "%PROJECT%"
    "%PYTHON%" -m src.embedding.build_vector_db
    IF ERRORLEVEL 1 (
        echo ERROR: Failed to build FAISS index.
        pause
        exit /b 1
    )
    echo FAISS index built successfully!
) ELSE (
    echo FAISS index found. Skipping build.
)

echo [3/4] Starting FastAPI backend (port 8000)...
start "Dharma Backend" cmd /k "cd /d "%PROJECT%" && "%PYTHON%" -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak > nul

echo [4/4] Starting React frontend (port 5173)...
start "Dharma Frontend" cmd /k "cd /d "%PROJECT%\frontend" && npm run dev"

echo.
echo ============================================================
echo   Dharma is starting up!
echo   Backend API: http://localhost:8000
echo   Frontend UI: http://localhost:5173
echo   API Docs:    http://localhost:8000/docs
echo ============================================================
echo.
echo Note: Make sure Ollama is running: ollama serve
echo.
pause
