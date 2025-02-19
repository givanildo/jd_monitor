@echo off
echo Configurando repositorio John Deere CAN Bus Monitor...

echo.
echo Criando estrutura de diretorios...
mkdir john-deere-canbus-monitor
cd john-deere-canbus-monitor
mkdir src\esp32
mkdir src\dashboard
mkdir docs\images
mkdir tests

echo.
echo Copiando arquivos para as pastas corretas...
copy ..\main.py src\esp32\
copy ..\web_server.py src\esp32\
copy ..\j1939_parser.py src\esp32\
copy ..\dashboard.py src\dashboard\
copy ..\README.md .

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

echo.
echo Inicializando Git...
git init
git add .
git commit -m "Primeiro commit: Monitor CAN Bus para Tratores John Deere"
git branch -M main

echo.
echo =============================================
echo Repositorio criado com sucesso!
echo.
echo Agora execute os seguintes comandos:
echo git remote add origin https://github.com/seu-usuario/john-deere-canbus-monitor.git
echo git push -u origin main
echo =============================================

pause 