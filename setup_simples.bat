@echo off
cls
color 0A

echo ========================================================
echo    Monitor CAN Bus - John Deere - Setup Simples
echo ========================================================
echo.

:: Verifica pasta atual
echo Pasta atual: %CD%
echo.

:: Remove pasta antiga se existir
if exist john-deere-canbus-monitor (
    echo Removendo pasta antiga...
    rmdir /s /q john-deere-canbus-monitor
    if errorlevel 1 (
        echo Erro ao remover pasta antiga!
        pause
        exit /b 1
    )
)

:: Cria diretórios um por um com verificação
echo Criando diretorios...
mkdir john-deere-canbus-monitor
if errorlevel 1 (
    echo Erro ao criar pasta principal!
    pause
    exit /b 1
)

cd john-deere-canbus-monitor
echo Criando src\esp32...
mkdir src\esp32
echo Criando src\dashboard...
mkdir src\dashboard
echo Criando docs\images...
mkdir docs\images
echo Criando tests...
mkdir tests

:: Copia arquivos com verificação
echo.
echo Copiando arquivos...
echo - Copiando main.py...
copy ..\main.py src\esp32\
echo - Copiando web_server.py...
copy ..\web_server.py src\esp32\
echo - Copiando j1939_parser.py...
copy ..\j1939_parser.py src\esp32\
echo - Copiando dashboard.py...
copy ..\dashboard.py src\dashboard\
echo - Copiando README.md...
copy ..\README.md .

:: Cria requirements.txt
echo.
echo Criando requirements.txt...
(
echo streamlit
echo pandas
echo plotly
echo folium
echo streamlit-folium
echo requests
echo mpremote
echo esptool
) > requirements.txt

:: Cria .gitignore
echo.
echo Criando .gitignore...
(
echo # Python
echo __pycache__/
echo *.py[cod]
echo *$py.class
echo .env
echo .venv
echo env/
echo venv/
) > .gitignore

:: Inicializa Git
echo.
echo Configurando Git...
git init
git add .
git commit -m "Primeiro commit: Monitor CAN Bus para Tratores John Deere"

echo.
echo ========================================================
echo                   Setup Concluido!
echo ========================================================
echo.
echo Estrutura criada em: %CD%
echo.
echo Proximo passo:
echo 1. Crie um repositorio no GitHub
echo 2. Execute os comandos:
echo    git remote add origin https://github.com/givanildo/john-deere-canbus-monitor.git
echo    git push -u origin main
echo.
pause 