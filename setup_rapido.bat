@echo off
cls
color 0A

echo Configurando repositorio...

:: Cria estrutura
mkdir john-deere-canbus-monitor
cd john-deere-canbus-monitor
mkdir src\esp32 src\dashboard docs\images tests

:: Copia arquivos
copy ..\main.py src\esp32\
copy ..\web_server.py src\esp32\
copy ..\j1939_parser.py src\esp32\
copy ..\dashboard.py src\dashboard\
copy ..\README.md .

:: Configura Git
git init
git config --global user.name "givanildo"
git config --global user.email "givanildobrunetta@gmail.com"
git add .
git commit -m "Primeiro commit"
git branch -M main
git remote add origin https://github.com/givanildo/john-deere-canbus-monitor.git

echo.
echo Agora cole seu token do GitHub
set /p token=Token: 
git remote set-url origin https://givanildo:%token%@github.com/givanildo/john-deere-canbus-monitor.git
git push -f -u origin main

echo.
echo Concluido!
pause 