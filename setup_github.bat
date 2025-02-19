@echo off
cls
color 0A

echo ========================================================
echo    Configuracao do GitHub - Monitor CAN Bus
echo ========================================================
echo.

:: Solicita informações do GitHub
set /p github_email=Digite seu email do GitHub: 
set /p github_token=Digite seu token do GitHub: 

:: Configura Git global
echo.
echo Configurando credenciais globais...
git config --global user.name "givanildo"
git config --global user.email "%github_email%"

:: Remove remote se existir
echo.
echo Removendo configuracoes antigas...
cd john-deere-canbus-monitor
git remote remove origin

:: Adiciona novo remote com token
echo.
echo Configurando novo remote com token...
git remote add origin https://givanildo:%github_token%@github.com/givanildo/john-deere-canbus-monitor.git

:: Tenta push
echo.
echo Enviando para o GitHub...
git push -u origin main

if errorlevel 1 (
    echo.
    echo ATENCAO: Erro ao fazer push!
    echo 1. Verifique se o repositorio existe: https://github.com/givanildo/john-deere-canbus-monitor
    echo 2. Verifique se o token esta correto
    echo 3. Tente novamente
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