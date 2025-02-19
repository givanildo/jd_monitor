@echo off
cls
color 0A

echo ========================================================
echo    Correcao e Setup do GitHub - Monitor CAN Bus
echo ========================================================
echo.

:: Verifica se está na pasta correta
if not exist "john-deere-canbus-monitor" (
    echo Pasta do projeto nao encontrada!
    echo Execute primeiro o setup_simples.bat
    pause
    exit /b 1
)

:: Entra na pasta do projeto
cd john-deere-canbus-monitor

:: Solicita informações do GitHub
set /p github_email=Digite seu email do GitHub: 
set /p github_token=Digite seu token do GitHub: 

:: Configura Git global
echo.
echo Configurando credenciais globais...
git config --global user.name "givanildo"
git config --global user.email "%github_email%"

:: Limpa configurações antigas
echo.
echo Limpando configuracoes antigas...
git remote remove origin
git reset --hard HEAD

:: Força reconfiguração do repositório
echo.
echo Reconfigurando repositorio...
git add .
git commit -m "Configuracao inicial: Monitor CAN Bus"
git branch -M main

:: Adiciona novo remote com token
echo.
echo Configurando novo remote com token...
git remote add origin https://givanildo:%github_token%@github.com/givanildo/john-deere-canbus-monitor.git

:: Força o push
echo.
echo Forcando push para o GitHub...
git push -f -u origin main

if errorlevel 1 (
    echo.
    echo ATENCAO: Erro ao fazer push!
    echo Verificando problemas...
    
    :: Tenta resolver problemas comuns
    echo.
    echo Tentando solucao alternativa...
    git pull origin main --allow-unrelated-histories
    git add .
    git commit -m "Merge: Resolucao de conflitos"
    git push -u origin main
    
    if errorlevel 1 (
        echo.
        echo ATENCAO: Ainda nao foi possivel fazer o push!
        echo 1. Verifique se criou o repositorio: https://github.com/givanildo/john-deere-canbus-monitor
        echo 2. Verifique se o token esta correto
        echo 3. Tente novamente
    )
) else (
    echo.
    echo ========================================================
    echo          Repositorio configurado com sucesso!
    echo ========================================================
    echo.
    echo Seu codigo esta disponivel em:
    echo https://github.com/givanildo/john-deere-canbus-monitor
)

echo.
pause 