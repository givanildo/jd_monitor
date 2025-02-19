@echo off
echo Criando estrutura de diretorios...
mkdir src\esp32
mkdir src\dashboard
mkdir docs\images
mkdir tests

echo Criando arquivos principais...
copy nul README.md
copy nul requirements.txt
copy nul LICENSE
copy nul src\esp32\main.py
copy nul src\esp32\web_server.py
copy nul src\esp32\j1939_parser.py
copy nul src\dashboard\dashboard.py

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
echo .Python
echo build/
echo develop-eggs/
echo dist/
echo downloads/
echo eggs/
echo .eggs/
echo lib/
echo lib64/
echo parts/
echo sdist/
echo var/
echo wheels/
echo *.egg-info/
echo .installed.cfg
echo *.egg
echo.
echo # IDEs
echo .idea/
echo .vscode/
echo *.swp
echo *.swo
echo.
echo # Sistema
echo .DS_Store
echo Thumbs.db
) > .gitignore

echo Inicializando repositorio Git...
git init
git add .
git commit -m "Primeiro commit: Monitor CAN Bus para Tratores"
git branch -M main

echo.
echo =============================================
echo Agora execute os seguintes comandos:
echo git remote add origin https://github.com/seu-usuario/john-deere-canbus-monitor.git
echo git push -u origin main
echo =============================================

pause 